import os
import yaml
import tarfile
import datetime
import time
from minio import Minio
from minio.error import ResponseError

def push_to_minio(bucket, path):
    home_dir = os.path.expanduser('~')
    lab_dir = os.path.join(home_dir, '.lab')

    with open(os.path.join(lab_dir, 'config.yaml'), 'r') as file:
        minio_config = yaml.load(file)

    with open(os.path.join(path, 'config/runtime.yaml'), 'r') as file:
        config = yaml.load(file)

    project_name = config['name']
    
    hostname = minio_config['minio_endpoint']
    accesskey = minio_config['minio_accesskey']
    secretkey = minio_config['minio_secretkey']

    input_objects = []
    output_objects = []
    exclude = set(['.venv'])
    for root, d_names, f_names in os.walk(path, topdown=True):
        d_names[:] = [d for d in d_names if d not in exclude]
        for f in f_names:
            input_objects.append(os.path.join(root, f))
            output_objects.append(os.path.join(project_name, root.strip('./'), f))

    minioClient = Minio(hostname,
                  access_key=accesskey,
                  secret_key=secretkey,
                  secure=False)

    if not minioClient.bucket_exists(bucket):
        minioClient.make_bucket(bucket, location='eu-west-1')

    try:
        for root, directories, filenames in os.walk(path):
            for i in range(len(input_objects)):                
                minioClient.fput_object(bucket, output_objects[i], input_objects[i])
    except ResponseError as err:
        print(err)