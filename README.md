# Offensive Speech Detection Service
<img width="703" alt="Screen Shot 2022-08-01 at 11 35 56 AM" src="https://user-images.githubusercontent.com/57039578/182186206-eb4cc417-380b-4d29-8041-3a99acbbc146.png">

This service is made up of two main components: the speech 2 text and the offensive/hate speech detection model.    
We utilized Amazon Transcribe, as it is a best in its class automatic speech recognition, to transcribe the videos as they land in the users input S3 bucket. This process is automatically triggered by a lambda funtion on the video upload and send the transcription to the offensive speech detection model.
The Offensive/hate speech detection uses a model derived from the hugging face model hub and served using AWS sagemaker endpoint to classify the transcriptions into hate speech, offensive speech or normal speech. The detected hate speech or offensive speech are then written to the output bucket with time stamps for the user app to process.    

### Modules:    
- **hate-speech-detection.ipynb:** Hate speech detection model from hugging face model hub deployed via Amazon Sagemaker endpoint.
- **transcribe_lambda_function.py:** Lambda funtion triggered by a file upload and performs automatic speech recognition (ASR) on the video.
- **speech_lambda_function.py:** Lambda funtion triggered by the output of the transcription and calls the offensive/hate speech detection models.


