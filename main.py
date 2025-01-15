import json
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
from urllib.parse import unquote
import uvicorn


app = FastAPI()
app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_methods=['*'],
)
load_dotenv()
BITRIX_SECRET = os.getenv('BITRIX_SECRET')
SC_TOKEN = os.getenv('SC_TOKEN')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post('/')
async def main(request: Request):
    body = await request.body()
    hook_parameters = unquote(body.decode()).split('&')
    hook_params_dict = {}
    for elem in hook_parameters:
        k, v = elem.split('=')
        hook_params_dict[k] = v
    task_id = hook_params_dict['data[FIELDS_AFTER][ID]']
    logger.info(f'{task_id=}')

    task_response = requests.get(
            f'https://crm.agneko.com/rest/{BITRIX_SECRET}/tasks.task.get?taskId={task_id}'
    ).json()
    task = task_response['result']['task']
    task_title = task['title']
    logger.info(f'Got task {task_title}')
    task_description = task['description']
    responsible_id = task['responsible']['id']
    logger.info(f'{responsible_id=}')

    user_response = requests.get(
            f'https://crm.agneko.com/rest/{BITRIX_SECRET}/user.get.json?ID={responsible_id}'
    ).json()
    user_email = user_response['result'][0]['EMAIL']
    logger.info(f'{user_email=}')

    task_item_response = requests.get(
            f'https://crm.agneko.com/rest/{BITRIX_SECRET}/task.item.getdata?taskId={task_id}'
    ).json()
    uf_crm_task = task_item_response.get('result').get('UF_CRM_TASK')
    lead_id = uf_crm_task[0].split('_')[-1]
    logger.info(f'{lead_id=}')

    lead_response = requests.get(
            f'https://crm.agneko.com/rest/{BITRIX_SECRET}/crm.lead.get?id={lead_id}'
    ).json()
    contact_id = lead_response.get('result').get('CONTACT_ID')
    logger.info(f'{contact_id=}')

    contact_response = requests.get(
            f'https://crm.agneko.com/rest/{BITRIX_SECRET}/crm.contact.get?id={contact_id}'
    ).json()
    contact_email = contact_response.get('result').get('EMAIL')[0].get('VALUE')
    logger.info(f'{contact_email=}')



    headers = {'authtoken': SC_TOKEN}
    list_info = {
        "list_info": {
            "row_count": "10",
            "start_index": "1",
            "sort_field": "name",
            "sort_order": "asc",
            "search_fields": {
                "name": contact_email.split('@')[-1]
            }
        }
    }
    params = {'input_data': json.dumps(list_info)}
    account_response = requests.get(
            url='https://support.agneko.com/api/v3/accounts',
            headers=headers, params=params, verify=False,
    ).json()
    account = account_response.get('accounts')[0]

    sdp_task = {
            'task': {
                'title': task['title'],
                'description': task['description'],
                'owner': {
                    'email_id': user_email,
                },
                'status': {
                    'name': 'Открыта'
                },
                'account': {
                    'id': account.get('id')
                },
                'udf_fields': {
                    'sline_bitrix_task_id': task_id
                }
            }
    }
    params = {'input_data': json.dumps(sdp_task)}
    sdp_task_response = requests.post(
            url='https://support.agneko.com/api/v3/tasks',
            headers=headers, params=params, verify=False,
    )
    print(sdp_task_response.json())



@app.post('/a')
async def a(request: Request):
    body = await request.body()
    hook_parameters = unquote(body.decode()).split('&')
    hook_params_dict = {}
    for elem in hook_parameters:
        k, v = elem.split('=')

        hook_params_dict[k] = v
    print(hook_parameters)


@app.post('/b')
async def b(request: Request):
    body = await request.body()
    hook_parameters = unquote(body.decode()).split('&')

def bb():
    hook_parameters = ['data[FIELDS_AFTER][TASK_ID]=8756', 'data[FIELDS_AFTER][ID]=36211']

    hook_params_dict = {}
    for elem in hook_parameters:
        k, v = elem.split('=')
        hook_params_dict[k] = v
        logger.info(elem)
    b_task_id = hook_params_dict['data[FIELDS_AFTER][TASK_ID]']
    b_task_comment_id = hook_params_dict['data[FIELDS_AFTER][ID]']

    b_task_comment_response = requests.get(
        f'https://crm.agneko.com/rest/{BITRIX_SECRET}/task.commentitem.get?taskId={b_task_id}&itemId={b_task_comment_id}'
    ).json()
    comment_result = b_task_comment_response.get('result')
    b_task_comment_text = comment_result.get('POST_MESSAGE')

    logger.info(b_task_comment_text)

def bb(b_task_id):
    list_info = {
        "list_info": {
            "row_count": "1",
            "search_fields": {
                    'udf_fields.sline_bitrix_task_id': b_task_id
            }
        }
    }
    headers = {'authtoken': SC_TOKEN}
    params = {'input_data': json.dumps(list_info)}
    sdp_task_response = requests.get(
            url='https://support.agneko.com/api/v3/tasks',
            headers=headers, params=params, verify=False,
    )
    logger.info(sdp_task_response.json())
    sc_task_id = sdp_task_response.json().get('tasks')[0].get('id')
    logger.info(f'{sc_task_id=}')

    task_update = {
        "task": {
            "status": {
                "name": "Закрыта"
            },
        }
    }
    params = {'input_data': json.dumps(list_info)}
    sdp_task_response = requests.put(
            url=f'https://support.agneko.com/api/v3/tasks/{sc_task_id}',
            headers=headers, params=params, verify=False,
    )

    

if __name__ == '__main__':
    bb(100)
    uvicorn.run('main:app',
                host='0.0.0.0',
                port=8000,
                log_level='info')
