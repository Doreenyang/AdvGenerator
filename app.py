from dotenv import load_dotenv
#from IPython.display import display, Image, Audio
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip
import cv2
#import rembg
#import base64
import io
import openai
import os
import requests
import streamlit as st
import tempfile
from PIL import Image
import numpy as np
from PIL import Image
#from deepface import DeepFace
from pydub import AudioSegment

load_dotenv()  # get secret API key

# Upload Image
def image_to_bytes(image):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmpfile:
        img = Image.open(image)
        img.save(tmpfile.name, 'JPEG')
        with open(tmpfile.name, 'rb') as f:
            return f.read()

# remove background
# def remove_background(image_bytes):
#     img = rembg.remove(image_bytes)
#     result_bytes = img
#     return result_bytes
    #return image_bytes

#Another way: use removebg API to remove background(better quality)
def remove_background(image_bytes):
    api_key = os.environ.get("REMOVE_BG_API_KEY")
    if not api_key:
        raise Exception("Remove.bg API key not found. Please set it in your environment variables.")

    url = "https://api.remove.bg/v1.0/removebg"
    headers = {"X-Api-Key": api_key}

    files = {"image_file": ("image.jpg", image_bytes)}

    response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to remove background. Status code: {response.status_code}. Response: {response.text}")
    

#Generate advertisement for the image 
def adv_gen(uploaded_image,product_name, product_description, prompt):
    PROMPT_MESSAGES=[
        {
            "role":"user",
            "content":[
                prompt,
                *map(lambda x:{"image":x, "resize":768},
                     uploaded_image),
            ],
        },
    ]
    params = {
        "model":"gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "api_key":os.environ["OPENAI_API_KEY"],
        "headers":{"Openai-Version": "2020-11-07"},
        "max_tokens":500,
    }
    result = openai.ChatCompletion.create(**params)
    #print(result.choices[0].message.content)
    return result.choices[0].message.content


# Generate voice for adv
def text_to_audio(text):
    response = requests.post(
        "https://api.openai.com/v1/audio/speech",
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        },
        json={
            "model": "tts-1",
            "input": text,
            "voice": "onyx", #voice option: alloy, echo, fable, onyx, nova, and shimmer
        },
    )
    #checj if the request was successful
    if response.status_code !=200:
        raise Exception("Request failed with status code")
    
    #Create an in-memory bytes buffer
    audio_bytes_io = io.BytesIO()

    #Write audio data to the in-memory bytes buffer
    for chunk in response.iter_content(chunk_size=1024*1024):
        audio_bytes_io.write(chunk)
        #Important: Seek to the start of the BytesIO buffer before returning
        audio_bytes_io.seek(0)
    #save audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmpfile:
        for chunk in response.iter_content(chunk_size=1024*1024):
            tmpfile.write(chunk)
        audio_filename = tmpfile.name

    return audio_filename, audio_bytes_io



# Merge video and audio together
def merge_audio_image(image_filename, audio_filename, output_filename):
    print("Merging audio and video...")
    #Load the image file
    video_clip = image_filename
    #load the audio file
    audio_clip = AudioFileClip(audio_filename)
    #Set the audio of the image as the audio file
    final_clip = video_clip.set_audio(audio_clip)
    #write the result to a file
    final_clip.write_videofile(
        output_filename,codec='libx264',audio_codec='aac'
    )
    #close the clip
    audio_clip.close
    


# Streamlit UI
def main():
    st.set_page_config(page_title="Generate Advertisement")
    st.header("Advertisement Generator")
    uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

    if uploaded_image is not None:
        st.image(uploaded_image)
        product_name = st.text_input("Product Name")
        product_description = st.text_area("Product Description")
        product_price = st.text_input("Product Price")
        prompt = st.text_area(
            "Prompt",
            value=f"You are the product {product_name}, and also the seller in Underground Dojo. Here's the product you are marketing: {product_description}. It is priced at {product_price}. You try to bring more customers. Generate an advertisement for yourself using the first person and personalize the product:"
        )

    if st.button('Generate') and uploaded_image is not None:
        with st.spinner('Processing...'):
            image_bytes = image_to_bytes(uploaded_image)
            # st.image(image_bytes, use_column_width=True)

            #remove background
            processed_image_bytes = remove_background(image_bytes)
            processed_image = Image.open(io.BytesIO(processed_image_bytes))

            st.image(processed_image)

            text = adv_gen(uploaded_image, product_name, product_description, prompt)

            # st.write("Generated Advertisement:")
            st.text_area(
                "Advertisement Text",
                text,
                key="output_text",
                help="Generated advertisement text",
            )

            # Generate voice from text
            audio_filename, audio_bytes_io = text_to_audio(text)

            # Save audio to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmpfile:
                tmpfile.write(audio_bytes_io.getvalue())
                output_audio_filename = tmpfile.name

            # Display the audio player
            st.audio(output_audio_filename, format='audio/wav', start_time=0)

            # Display the audio link
            st.markdown(f"**Generated Audio:** [Download Audio]({output_audio_filename})")

            #image_array = np.array(Image.open(io.BytesIO(image_bytes)))
            image_array = np.array(processed_image)

            # Set the length of the video to be the same as the audio's length
            audio_duration = AudioFileClip(output_audio_filename).duration
            image_clip = ImageClip(image_array, duration=audio_duration)

            # Set the fps attribute for the video clip
            image_clip.fps = 24

            # Save the video without audio
            output_video_filename = os.path.splitext(product_name)[0] + '_output.mp4'
            image_clip.write_videofile(output_video_filename, codec='libx264')

            # Display the video
            with open(output_video_filename, 'rb') as video_file:
                video_contents = video_file.read()
                st.video(video_contents, format="video/mp4", start_time=0)

            # Display the video link
            st.markdown(f"**Generated Video:** [Download Video]({output_video_filename})")


if __name__ == '__main__':
    main()





