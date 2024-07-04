from unittest.mock import MagicMock
from aiohttp import web
import pytest
from database import CustomBase
from handlers import (
    ConcreteHandler,  # Certifique-se de importar ConcreteHandler aqui
    CreateHandler,
    ReadHandler,
    UpdateHandler,
    PatchHandler,
    DeleteHandler,
    RetrieveAllHandler,
    OptionsHandler,
    HeadHandler,
)

@pytest.fixture
def mock_model():
    return MagicMock(spec=CustomBase)

@pytest.fixture
def mock_request():
    return MagicMock(spec=web.Request)

@pytest.fixture
def session(db):
    return db

def test_concrete_handler_initialization(mock_model):
    concrete_handler = ConcreteHandler(model=mock_model)
    assert concrete_handler.model == mock_model

async def test_concrete_handler_call(session, mock_request):
    mock_handler = MagicMock(spec=ConcreteHandler)

    concrete_handler = ConcreteHandler()
    concrete_handler.handle = mock_handler.handle
    response = await concrete_handler(mock_request)

    assert response == mock_handler.handle.return_value


def test_create_handler_initialization(mock_model):
    create_handler = CreateHandler(model=mock_model)
    assert create_handler.model == mock_model

async def test_create_handler_handle_success(session, mock_request, mock_model):
    data = {"name": "Test Item"}
    mock_request.json.return_value = data
    create_handler = CreateHandler(model=mock_model)
    response = await create_handler.handle(session, mock_request)

    session.add.assert_called_once()
    session.commit.assert_called_once()
    assert session.refresh.called
    assert response.status == 201

async def test_create_handler_handle_invalid_data(session, mock_request, mock_model):
    invalid_data = {"invalid_field": "Invalid Value"}
    mock_request.json.return_value = invalid_data
    create_handler = CreateHandler(model=mock_model)
    response = await create_handler.handle(session, mock_request)

    assert not session.add.called
    assert not session.commit.called
    assert not session.refresh.called
    assert response.status == 400

def test_read_handler_initialization(mock_model):
    read_handler = ReadHandler(model=mock_model)
    assert read_handler.model == mock_model

async def test_read_handler_retrieve_all(session, mock_request, mock_model):
    mock_query = MagicMock()
    session.query.return_value = mock_query
    mock_items = [mock_model(pk=1), mock_model(pk=2)]
    mock_query.all.return_value = mock_items

    read_handler = ReadHandler(model=mock_model)
    response = await read_handler.handle(session, mock_request)

    session.query.assert_called_once_with(mock_model)
    assert response.status == 200
    assert response.body == web.json_response([item.as_dict() for item in mock_items]).body

async def test_read_handler_retrieve_one_success(session, mock_request, mock_model):
    mock_item = mock_model(pk=1)
    session.query.return_value.filter.return_value.first.return_value = mock_item

    mock_request.match_info = {"id": "1"}

    read_handler = ReadHandler(model=mock_model)
    response = await read_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    assert response.status == 200
    assert response.body == web.json_response(mock_item.as_dict()).body

async def test_read_handler_retrieve_one_not_found(session, mock_request, mock_model):
    session.query.return_value.filter.return_value.first.return_value = None

    mock_request.match_info = {"id": "1"}

    read_handler = ReadHandler(model=mock_model)
    response = await read_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    assert response.status == 404
    assert response.body == web.json_response({'error': 'Item not found'}, status=404).body

def test_update_handler_initialization(mock_model):
    update_handler = UpdateHandler(model=mock_model)
    assert update_handler.model == mock_model

async def test_update_handler_update_success(session, mock_request, mock_model):
    mock_item = mock_model(pk=1)
    session.query.return_value.filter.return_value.first.return_value = mock_item

    data = {"name": "Updated Name"}
    mock_request.match_info = {"id": "1"}
    mock_request.json.return_value = data

    update_handler = UpdateHandler(model=mock_model)
    response = await update_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    assert mock_item.name == "Updated Name"
    session.commit.assert_called_once()
    assert session.refresh.called
    assert response.status == 200
    assert response.body == web.json_response(mock_item.as_dict()).body

async def test_update_handler_update_not_found(session, mock_request, mock_model):
    session.query.return_value.filter.return_value.first.return_value = None

    data = {"name": "Updated Name"}
    mock_request.match_info = {"id": "1"}
    mock_request.json.return_value = data

    update_handler = UpdateHandler(model=mock_model)
    response = await update_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    assert response.status == 404
    assert response.body == web.json_response({'error': 'Item not found'}, status=404).body

def test_patch_handler_initialization(mock_model):
    patch_handler = PatchHandler(model=mock_model)
    assert patch_handler.model == mock_model

async def test_patch_handler_patch_success(session, mock_request, mock_model):
    mock_item = mock_model(pk=1)
    session.query.return_value.filter.return_value.first.return_value = mock_item

    data = {"name": "Updated Name"}
    mock_request.match_info = {"id": "1"}
    mock_request.json.return_value = data

    patch_handler = PatchHandler(model=mock_model)
    response = await patch_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    assert mock_item.name == "Updated Name"
    session.commit.assert_called_once()
    assert session.refresh.called
    assert response.status == 200
    assert response.body == web.json_response(mock_item.as_dict()).body

async def test_patch_handler_patch_not_found(session, mock_request, mock_model):
    session.query.return_value.filter.return_value.first.return_value = None

    data = {"name": "Updated Name"}
    mock_request.match_info = {"id": "1"}
    mock_request.json.return_value = data

    patch_handler = PatchHandler(model=mock_model)
    response = await patch_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    assert response.status == 404
    assert response.body == web.json_response({'error': 'Item not found'}, status=404).body

def test_delete_handler_initialization(mock_model):
    delete_handler = DeleteHandler(model=mock_model)
    assert delete_handler.model == mock_model

async def test_delete_handler_delete_success(session, mock_request, mock_model):
    mock_item = mock_model(pk=1)
    session.query.return_value.filter.return_value.first.return_value = mock_item

    mock_request.match_info = {"id": "1"}

    delete_handler = DeleteHandler(model=mock_model)
    response = await delete_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    session.delete.assert_called_once_with(mock_item)
    session.commit.assert_called_once()
    assert response.status == 204

async def test_delete_handler_delete_not_found(session, mock_request, mock_model):
    session.query.return_value.filter.return_value.first.return_value = None

    mock_request.match_info = {"id": "1"}

    delete_handler = DeleteHandler(model=mock_model)
    response = await delete_handler.handle(session, mock_request)

    session.query.return_value.filter.assert_called_once_with(mock_model.pk == 1)
    assert response.status == 404
    assert response.body == web.json_response({'error': 'Item not found'}, status=404).body

def test_retrieve_all_handler_initialization(mock_model):
    retrieve_all_handler = RetrieveAllHandler(model=mock_model)
    assert retrieve_all_handler.model == mock_model

async def test_retrieve_all_handler_retrieve_all(session, mock_request, mock_model):
    mock_query = MagicMock()
    session.query.return_value = mock_query
    mock_items = [mock_model(pk=1), mock_model(pk=2)]
    mock_query.all.return_value = mock_items

    retrieve_all_handler = RetrieveAllHandler(model=mock_model)
    response = await retrieve_all_handler.handle(session, mock_request)

    session.query.assert_called_once_with(mock_model)
    assert response.status == 200
    assert response.body == web.json_response([item.as_dict() for item in mock_items]).body

def test_options_handler_initialization(mock_model):
    options_handler = OptionsHandler(model=mock_model)
    assert options_handler.model == mock_model

async def test_options_handler_options(session, mock_request, mock_model):
    options_handler = OptionsHandler(model=mock_model)
    response = await options_handler.handle(session, mock_request)

    assert response.status == 200
    assert response.body == web.json_response(
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
    ).body

def test_head_handler_initialization(mock_model):
    head_handler = HeadHandler(model=mock_model)
    assert head_handler.model == mock_model

async def test_head_handler_head(session, mock_request, mock_model):
    head_handler = HeadHandler(model=mock_model)
    response = await head_handler.handle(session, mock_request)

    assert response.status == 200
    assert response.body == web.Response(
        status=200, headers={'Content-Type': 'application/json'}
    ).body


