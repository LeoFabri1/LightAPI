import logging
from abc import abstractmethod, ABC
from dataclasses import dataclass, field

from sqlalchemy.orm import Session
from database import SessionLocal, CustomBase
from aiohttp import web


def create_handler(model: CustomBase):
    return [
        web.post(f'/{model.__tablename__}/', CreateHandler(model)),
        web.get(f'/{model.__tablename__}/', RetrieveAllHandler(model)),
        web.get(f'/{model.__tablename__}/{{id}}', ReadHandler(model)),
        web.put(f'/{model.__tablename__}/{{id}}', UpdateHandler(model)),
        web.delete(f'/{model.__tablename__}/{{id}}', DeleteHandler(model)),
        web.patch(f'/{model.__tablename__}/{{id}}', PatchHandler(model)),
        web.options(f'/{model.__tablename__}/', OptionsHandler(model)),
        web.head(f'/{model.__tablename__}/', HeadHandler(model)),
    ]


@dataclass
class AbstractHandler(ABC):
    model: CustomBase = field(default=None)

    @abstractmethod
    async def handle(self, db: Session, request: web.Request):
        """Método para manipular a requisição."""
        raise NotImplementedError("Method not implemented")

    async def __call__(self, request: web.Request, *args, **kwargs):
        db: Session = SessionLocal()
        try:
            return await self.handle(db, request)
        finally:
            db.close()

    async def get_request_json(self, request: web.Request):
        """Obtém os dados JSON da requisição."""
        return await request.json()

    def get_item_by_id(self, db: Session, item_id: int):
        """Obtém um item pelo ID."""
        return db.query(self.model).filter(self.model.pk == item_id).first()

    def add_and_commit_item(self, db: Session, item):
        """Adiciona um item ao banco de dados e faz commit."""
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def delete_and_commit_item(self, db: Session, item):
        """Exclui um item do banco de dados e faz commit."""
        db.delete(item)
        db.commit()

    def json_response(self, item, status=200):
        """Retorna uma resposta JSON."""
        return web.json_response(item.as_dict(), status=status)

    def json_error_response(self, error_message, status=404):
        """Retorna uma resposta de erro JSON."""
        return web.json_response({'error': error_message}, status=status)

class ConcreteHandler(AbstractHandler):
    async def handle(self, db, request):
        # Implementação do método handle
        return web.Response(text="Handled request")


class CreateHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a criação de um novo item."""
        data = await self.get_request_json(request)
        item = self.model(**data)
        item = self.add_and_commit_item(db, item)
        return self.json_response(item, status=201)


class ReadHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a leitura de um item ou de todos os itens."""
        if 'id' not in request.match_info:
            items = db.query(self.model).all()
            response = [item.as_dict() for item in items]
            return self.json_response(response, status=200)
        else:
            item_id = int(request.match_info['id'])
            item = self.get_item_by_id(db, item_id)
            if item:
                return self.json_response(item, status=200)
            else:
                return self.json_error_response('Item not found', status=404)


class UpdateHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a atualização de um item."""
        item_id = int(request.match_info['id'])
        item = self.get_item_by_id(db, item_id)
        if not item:
            return self.json_error_response('Item not found', status=404)

        data = await self.get_request_json(request)
        for key, value in data.items():
            setattr(item, key, value)

        item = self.add_and_commit_item(db, item)
        return self.json_response(item, status=200)


class PatchHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a atualização parcial de um item."""
        item_id = int(request.match_info['id'])
        item = self.get_item_by_id(db, item_id)
        if not item:
            return self.json_error_response('Item not found', status=404)

        data = await self.get_request_json(request)
        for key, value in data.items():
            setattr(item, key, value)

        item = self.add_and_commit_item(db, item)
        return self.json_response(item, status=200)


class DeleteHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a exclusão de um item."""
        item_id = int(request.match_info['id'])
        item = self.get_item_by_id(db, item_id)
        if not item:
            return self.json_error_response('Item not found', status=404)

        self.delete_and_commit_item(db, item)
        return web.Response(status=204)


class RetrieveAllHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a recuperação de todos os itens."""
        items = db.query(self.model).all()
        response = [item.as_dict() for item in items]
        return web.json_response(response, status=200)


class OptionsHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a requisição de opções."""
        return web.json_response(
            {
                'allowed_methods': [
                    'GET',
                    'POST',
                    'PUT',
                    'DELETE',
                    'PATCH',
                    'OPTIONS',
                    'HEAD',
                ],
                'allowed_headers': ['Content-Type', 'Authorization'],
                'max_age': 3600,
            }
        )


class HeadHandler(AbstractHandler):
    async def handle(self, db, request):
        """Manipula a requisição HEAD."""
        return web.Response(
            status=200, headers={'Content-Type': 'application/json'}
        )
