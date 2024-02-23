import azure.functions as func
import logging
import requests
import os
import json
import urllib.parse
import time 

# https://learn.microsoft.com/en-us/azure/ai-services/translator/document-translation/how-to-guides/use-rest-api-programmatically?tabs=python#translate-a-specific-document-in-a-container
# https://learn.microsoft.com/en-us/azure/ai-services/translator/document-translation/how-to-guides/use-rest-api-programmatically?tabs=csharp



def extract_file_name_without_extension(blob_url):
    # Parse the blob URL
    parsed_url = urllib.parse.urlparse(blob_url)

    # Extract the path component and get the file name
    file_name_with_extension = os.path.basename(parsed_url.path)

    # Decode URL-encoded characters in the file name
    file_name_with_extension = urllib.parse.unquote(file_name_with_extension)

    # Split the file name into base name and extension
    base_name, file_extension = os.path.splitext(file_name_with_extension)

    return base_name


def construct_target_base_url(blob_url):
    # Parse the blob URL
    parsed_url = urllib.parse.urlparse(blob_url)

    # Extract the container URL (base URL) without the file name
    container_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(parsed_url.path.split('/')[:-1])}/"

    return container_url


app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trig_translator_dap_demo")
def http_trig_translator_dap_demo(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    endpoint = 'https://pag-azje-translator.cognitiveservices.azure.com/'
    key =  '3835565c76a740938977be0adaf7b347'

    blob_url = req.params.get('blob_url')

    file_name_without_extension = extract_file_name_without_extension(blob_url)

    converted_file_name = file_name_without_extension + "-eng.xlsx"

    path_single_file = "translator/text/batch/v1.1/batches"
    constructed_url_single_file = endpoint + path_single_file


    sourceSASUrl = f'{blob_url}?sp=racwdli&st=2024-01-17T15:06:16Z&se=2030-01-17T23:06:16Z&spr=https&sv=2022-11-02&sr=c&sig=QnA7iJHfnUk%2Fg12NpUTQIxcOYg6CAe1%2BwSPYKPHZHQY%3D'

    # Dynamically construct the target base URL
    target_base_url = construct_target_base_url(blob_url)
  
    targetSASUrl = f'{target_base_url}{converted_file_name}?sp=racwdli&st=2024-01-17T15:06:16Z&se=2030-01-17T23:06:16Z&spr=https&sv=2022-11-02&sr=c&sig=QnA7iJHfnUk%2Fg12NpUTQIxcOYg6CAe1%2BwSPYKPHZHQY%3D'

    return_target_url = f'{target_base_url}{converted_file_name}'

    body_single_file = {
        "inputs": [
            {
                "storageType": "File",
                "source": {
                    "sourceUrl": sourceSASUrl,
                    "storageSource": "AzureBlob",
                    "language": "ja"
                },
                "targets": [
                    {
                        "targetUrl": targetSASUrl,
                        "storageSource": "AzureBlob",
                        "category": "general",  
                        "language": "en",
                        "glossaries": [
                            {
                                "glossaryUrl": "https://blobpagstorage.blob.core.windows.net/glossary/glossary_sample.csv",
                                "format": "csv"
                            }
                        ]

                    }
                ]
            }
        ]
    }
    headers_single_file = {
    'Ocp-Apim-Subscription-Key': key,
    'Content-Type': 'application/json',
    }

    response_single_file = requests.post(constructed_url_single_file, headers=headers_single_file, json=body_single_file)

    if response_single_file.status_code == 200 or response_single_file.status_code == 202:
        # Add a time delay of 2.5 seconds
        time.sleep(2.5)

        result = [{
        'status': 'Success',
        'status_code': 200,
        'targetSASurl': return_target_url,
        }]
        # return func.HttpResponse(result)

    else:
        result = [{
        'status': 'Fail',
        'status_code': response_single_file.status_code,
        'targetSASurl': '',
        }]
        # return func.HttpResponse(result)

# Convert the result to a JSON string
    json_result = json.dumps(result)

    # Return the JSON string as an HTTP response
    return func.HttpResponse(json_result, mimetype="application/json")

