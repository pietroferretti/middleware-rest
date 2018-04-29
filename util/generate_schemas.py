from webapp.app import *

folder = 'webapp/schema_test/'

main_template_head = '''{{
    "url_template": "{url}",
    "template_parameters": [{params}],
    "actions": ['''

main_template_tail = '''
    ]
}
'''

param_template = '''
        {{
            "{param}": {{
                "type": "integer",
                "entity": "http://entities.backtoschool.io/someid"
            }}
        }}'''

get_template = '''
        {
            "method": "GET",
            "outputschema": {
                "$schema": "http://json-schema.org/draft-06/schema#",
                "type": "null"
            }
        }'''

post_template = '''
        {
            "method": "POST",
            "inputschema": {
                "$schema": "http://json-schema.org/draft-06/schema#",
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "entity": "http://entities.backtoschool.io/username"
                    },
                    "password": {
                        "type": "string",
                        "entity": "http://entities.backtoschool.io/password"
                    }
                },
                "required": ["username", "password"]
            },
            "outputschema": {
                "$schema": "http://json-schema.org/draft-06/schema#",
                "type": "null"
            }
        }'''

put_template = '''
        {
            "method": "PUT",
            "inputschema": {
                "$schema": "http://json-schema.org/draft-06/schema#",
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "entity": "http://entities.backtoschool.io/username"
                    },
                    "password": {
                        "type": "string",
                        "entity": "http://entities.backtoschool.io/password"
                    }
                },
                "required": ["username", "password"]
            },
            "outputschema": {
                "$schema": "http://json-schema.org/draft-06/schema#",
                "type": "null"
            }
        }'''


for rule in app.url_map.iter_rules():

    endpoint = rule.endpoint

    if endpoint in ('index', 'schema', 'static'):
        continue

    # url template
    url_template = str(rule)
    url_template = url_template.replace('<int:', '{')
    url_template = url_template.replace('<path:', '{')
    url_template = url_template.replace('>', '}')
    print(url_template)

    # parameters
    parameters = rule.arguments

    # methods
    methods = [x for x in rule.methods if x not in ('HEAD', 'OPTIONS')]

    # create schema
    params = ''
    for p in parameters:
        params += param_template.format(param=p)
        params += ','
    params = params.strip(',')
    if params:
        params += '\n    '

    schema = main_template_head.format(url=url_template, params=params)
    for m in methods:
        if m == 'GET':
            schema += get_template + ','
        elif m == 'POST':
            schema += post_template + ','
        elif m == 'PUT':
            schema += put_template + ','
        else:
            raise ValueError(m)
    schema = schema.strip(',')
    schema += main_template_tail

    # write to file
    filename = endpoint.replace('_', '-') + '-schema.json'
    with open(folder + filename, 'w') as f:
        f.write(schema)