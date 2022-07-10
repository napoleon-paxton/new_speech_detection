import boto3
import uuid
import json
import os
import io
import csv

def lambda_handler(event, context):
    # Take S3 dump event of transcribed text
    record = event['Records'][0]
    s3bucket = record['s3']['bucket']['name']
    s3object = record['s3']['object']['key']
    
    s3Path = "s3://" + s3bucket + "/" + s3object
    jobName = s3object + '-' + str(uuid.uuid4())
    
    # Connect to s3 bucket
    BUCKET_NAME = 'capstone-video-output' # replace with your bucket name
    # Initialize AWS client
    s3_client = boto3.client("s3")
    
    # Perform processing on only .srt subtitle files
    if '.srt' in s3object:
        # Read in data
        file_content = s3_client.get_object(
            Bucket=s3bucket, Key=s3object)["Body"].read()
        
        # Hate Speech Detection
        # Preprocess data
        def text_prep(text):
            '''
            Parses the input srt file and 
            returns a dict {time: sentence}
            '''
            text = str(text, 'utf-8')
            
            out = [i for i in text.split('\n') if len(i) > 3]
            out_dict = {}
            # Extract non empty sentences and time stamp
            for i in range(len(out)):
                if out[i][:3] == '00:' and out[i+1][:3] != '00:':
                    out_dict[out[i]] = out[i+1]

            return out_dict
            
        body = text_prep(file_content)
        
        ENDPOINT_NAME = 'huggingface-hate-speech-v3'
        runtime= boto3.client('runtime.sagemaker')
        
        # Detect hate speech for each sentence in the input
        ####
        # Detection Format: dict {start_time: (detection_type, sentence)}
        # detection_type: hate speech or offensive speech
        ####
        def detect_speech(text):
          '''
          Takes the body Json structure and returns the detected hate speech output
          '''
          detect = {}
          hate_count = 0
          offensive_count = 0
          for k, v in text.items():
            inp = {'inputs': str(v)}
            inp = json.dumps(inp).encode('utf-8')
            response = runtime.invoke_endpoint(EndpointName=ENDPOINT_NAME,
                                            ContentType='application/json',
                                            Body=inp)
            out = json.loads(response['Body'].read().decode())[0]
            
            time = k.split()[0]
            
            if out['label'] == 'hate speech':
              print(f'------Hate Speech Detected!------\n{v}\n')
              detect[time] = ('hate', v)
              hate_count += 1
        
            elif out['label'] == 'offensive':
              print(f'------Offensive Speech Detected!------\n{v}\n')
              detect[time] = ('offensive', v)
              offensive_count += 1
          
          # Write to S3 output
          file_name = f"{s3object.split('.')[0]}"
          out_bucket = f'equitable-surveillance-processed-output-speech'
          
          for time, body in detect.items():
            write_content = f'{body[0]}: {body[1]}' 
            
            MIN = time.split(':')[1]
            SEC = time.split(':')[2].split(',')[0]
            key_name = f'{file_name}/{MIN}_{SEC}_{file_name}.txt'
            s3_client.put_object(Bucket=out_bucket, Key=key_name, Body=write_content)
          
          write_content = f'{hate_count} Hate Speech Detected.\n{offensive_count} Offensive Speech Detected.'
          key_name = f'{file_name}/summary_{file_name}.txt'
          s3_client.put_object(Bucket=out_bucket, Key=key_name, Body=write_content)
          
          return detect
          
        final_output = detect_speech(body)
    
        return final_output
        
    else:
        return {
            "error": "S3 Upload not an .srt subtitle"
        }