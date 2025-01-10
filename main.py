import json
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


@app.post('/')
async def main(request: Request):
    body = await request.body()
    hook_parameters = unquote(body.decode()).split('&')
    hook_params_dict = {}
    for elem in hook_parameters:
        k, v = elem.split('=')
        hook_params_dict[k] = v
    task_id = hook_params_dict['data[FIELDS_AFTER][ID]']

    CRM_URL = f'https://crm.agneko.com/rest/{BITRIX_SECRET}'

    task_response = requests.get(f'{CRM_URL}/tasks.task.get?taskId={task_id}')
    task = task_response.json().get('result').get('task')
    responsible_id = task.get('responsible').get('id')
    user_response = requests.get(f'{CRM_URL}/user.get.json?ID={responsible_id}')
    user_email = user_response.json().get('result')[0].get('EMAIL')
    task_item_response = requests.get(f'{CRM_URL}/task.item.getdata?taskId={task_id}')
    uf_crm_task = task_item_response.json().get('result').get('UF_CRM_TASK')
    lead_id = uf_crm_task[0].split('_')
    lead_response = requests.get(f'{CRM_URL}/crm.lead.get?id={lead_id}')
    contact_id = lead_response.json().get('result').get('CONTACT_ID')
    contact_response = requests.get(f'{CRM_URL}/crm.lead.get?id={lead_id}')
    contact_email = contact_response.json().get('result').get('EMAIL').get('VALUE')
    
    print(contact_email)

    sdp_task = {
            'task': {
                'title': task['title'],
                'description': task['description'],
                'owner': {

                    'email_id': user_email,
                },
                'status': {
                    'name': 'Открыта'
                }
            }
    }

    params = {'input_data': json.dumps(sdp_task)}
    headers = {'authtoken': SC_TOKEN}
    sdp_task_response = requests.post(
            url='https://support.agneko.com/api/v3/tasks',
            headers=headers, params=params, verify=False,
    )
    print(sdp_task_response.json())


if __name__ == '__main__':
    uvicorn.run('main:app',
                host='0.0.0.0',
                port=8000,
                log_level='info')
