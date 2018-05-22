import json
import boto3
import os
import time
import hashlib
from random import randint, sample, shuffle
import math

boto_client = boto3.client('dynamodb')

TASKS = ["simple_task", "fibonacci", "sector_area", "last_task"]
LAST_TASK_LINK = 'https://youtu.be/9hC2jVypsuc'
SCHEME = 'https'
ASSIGNMENT_ID = 'd5d97fc3e3ed57ea'

WORDS = [
    "clotter",
    "Odyssey",
    "linea",
    "dither",
    "vaginule",
    "browden",
    "pampero",
    "setup",
    "acarine",
    "Mohican",
    "Aplysia",
    "dodoism",
    "unboat",
    "gether",
    "terzo",
    "litter",
    "carbona",
    "ozonous",
    "mullet",
    "anyway",
    "myiasis",
    "fourrier",
    "Pahareen",
    "Landwehr",
    "tucum",
    "leant",
    "locality",
    "thallome",
    "enshield",
    "cowpen",
    "muricate",
    "vaguely",
    "raffery",
    "kreplech",
    "fretways",
    "horner",
    "lubber",
    "inlook",
    "semiroll",
    "totty",
    "glycine",
    "wangler",
    "chemist",
    "unceased",
    "chocker",
    "stele",
    "matfelon",
    "potoo",
    "twicer",
    "paetrick",
    "sialidan",
    "avulse",
    "blackboy",
    "Streltzi",
    "ungrayed",
    "tierlike",
    "lornness",
    "poemlet",
    "fantail",
    "mouille",
    "moider",
    "ramplor",
    "Wanyoro",
    "smirk",
    "carrel",
    "ransomer",
    "unspan",
    "jerque",
    "uretal",
    "veily",
    "runny",
    "undefied",
    "cleaver",
    "parnel",
    "phalange",
    "Acropora",
    "barra",
    "sural",
    "onhanger",
    "quirkish",
    "Latinize",
    "sheered",
    "aroar",
    "unhacked",
    "tylion",
    "multiped",
    "faradic",
    "Amazona",
    "motey",
    "ratter",
    "casklike",
    "skeely",
    "anaphyte",
    "ergotin",
    "normless",
    "sware",
    "limbo",
    "winddog",
    "grease",
    "Macleaya",
    ]


class TaskNotFoundException(Exception):
    pass


def load_task(task_id):
    task_item = boto_client.get_item(
        TableName="tasksTable",
        Key={
            "ID": {
                "S": task_id
            }
        }
    )

    if 'Item' not in task_item:
        raise TaskNotFoundException

    task_item = task_item['Item']

    if int(task_item['ttl']['N']) - int(time.time()) <= 0:
        raise TaskNotFoundException

    task = {
        'name': task_item['name']['S'],
        'descr': task_item['descr']['S'],
        'params': json.loads(task_item['params']['S']),
        'answer': task_item['answer']['S'],
        'ttl': int(task_item['ttl']['N'])
    }

    return task


def create_task(task_name, ttl=30):
    task_func = globals()[task_name]

    descr = task_func.__doc__
    task_id = hashlib.sha1(os.urandom(8)).hexdigest()[:8]
    expires = int(time.time()) + ttl
    params, answer = task_func()

    boto_client.put_item(
        TableName="tasksTable",
        Item={
            'ID': {'S': task_id},
            'ttl': {'N': str(expires)},
            'name': {'S': task_name},
            'descr': {'S': descr},
            'params': {'S': json.dumps(params)},
            'answer': {'S': answer}
        }
    )

    return task_id


def get_task_link(event, task_id):
    return '{}://{}/{}/tasks/{}'.format(
        SCHEME,
        event['headers']['Host'],
        ASSIGNMENT_ID,
        task_id
    )


def get_task(event, context):
    task_id = event['pathParameters']['id']

    try:
        task = load_task(task_id)
        response_body = {
            'description': task['descr'],
            'parameters': task['params'],
            'selfLink': get_task_link(event, task_id),
            'ttl': task['ttl'] - int(time.time())
        }

        response = {
            "statusCode": 200,
            "body": json.dumps(response_body, indent=4),
            "headers": {
                'access-control-allow-origin': '*',
                'access-control-allow-headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
                'access-control-allow-methods': 'OPTIONS,GET,POST',
                'access-control-allow-credentials': 'false',
            }
        }

    except TaskNotFoundException:
        response = {
            "statusCode": 404
        }

    return response


def post_task(event, context):
    body = json.loads(event['body'])
    task_id = event['pathParameters']['id']

    try:
        task = load_task(task_id)
    except TaskNotFoundException:
        return {
            "statusCode": 404
        }

    print('{} - {} - {} - {}'.format(task['name'], task['answer'], body['answer'], body['answer'] == task['answer']))
    
    if body['answer'] != task['answer']:
        return {
            "statusCode": 200,
            "body": json.dumps({
                'checkResult': False
            }, indent=4),
            "headers": {
                'access-control-allow-origin': '*',
                'access-control-allow-headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
                'access-control-allow-methods': 'OPTIONS,GET,POST',
                'access-control-allow-credentials': 'false',
            }
        }

    next_task_index = TASKS.index(task['name']) + 1
    if next_task_index == len(TASKS):
        next_task_link = LAST_TASK_LINK
    else:
        next_task_id = create_task(TASKS[next_task_index])
        next_task_link = get_task_link(event, next_task_id)

    return {
        "statusCode": 200,
        "body": json.dumps({
            'checkResult': True,
            'nextTaskLink': next_task_link
        }, indent=4),
        "headers": {
            'access-control-allow-origin': '*',
            'access-control-allow-headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
            'access-control-allow-methods': 'OPTIONS,GET,POST',
            'access-control-allow-credentials': 'false',
        }
    }


def get_started(event, context):
    task_id = create_task(TASKS[0])

    response = {
        "statusCode": 302,
        "headers": {
            'Location': get_task_link(event, task_id),
            'access-control-allow-origin': '*',
            'access-control-allow-headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent',
            'access-control-allow-methods': 'OPTIONS,GET',
            'access-control-allow-credentials': 'false',
        }
    }

    return response


def simple_task():
    """What is the sum of a and b?"""

    max_js_int = 2**53 - 1
    result = randint(0, max_js_int)
    a = randint(0, result)
    b = result - a

    return (
        {
            'a': a,
            'b': b
        },
        str(result)
    )


def sector_area():
    """What is the area of a sector with radius r, arc length
       L and angle PHI (in radians)?"""

    r = randint(0, 65535)
    p = 2 * math.pi * r
    L = randint(0, int(p))

    if (r*L) % 2 == 0:
        fmt_str = '{:.0f}'
    else:
        fmt_str = '{:.1f}'

    A = r*L/2.0

    return (
        {
            'r': r,
            'L': L,
            'PHI': '{:.2f}'.format(2*A/(r*r))
        },
        fmt_str.format(A)
    )


def fibonacci():
    """What is the greatest Fibonacci number less than N?"""

    N = randint(1, 2**53 - 1)

    a, b = 0, 1

    while b < N:
        a, b = b, a + b

    return (
        {
            'N': N
        },
        str(a)
    )


def last_task():
    """What is the shortest word in array A?"""

    arr = ['Gaza'] + sample(WORDS, 14)
    shuffle(arr)

    return (
        {
            'A': arr
        },
        'Gaza'
    )
