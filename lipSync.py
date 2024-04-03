import cv2
import numpy as np

# Load the monster image
monster_image_path = 'bob.jpeg'
monster_image = cv2.imread(monster_image_path)

# Output video file
output_video_name = 'output_video_lip_sync.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Change the codec to XVID
video_out = cv2.VideoWriter(output_video_name, fourcc, 30, (monster_image.shape[1], monster_image.shape[0]), isColor=True)

# Lip sync timing (for demonstration purposes)
lip_sync_timing = [10, 20, 30]  # Adjust as needed

# Open and close mouth animation
for frame_number in range(1, 101):  # Assuming 100 frames in the video
    frame = np.copy(monster_image)

    # Determine the mouth status for the current frame
    is_mouth_open = frame_number in lip_sync_timing

    # Simulate mouth opening and closing
    if is_mouth_open:
        # Modify the region of the mouth to simulate opening
        frame[50:100, 50:150] = [255, 255, 255]  # White color represents an open mouth
    else:
        # Modify the region of the mouth to simulate closing
        frame[50:100, 50:150] = [0, 0, 0]  # Black color represents a closed mouth

    # Write the frame to the output video
    video_out.write(frame)

# Release the video writer
video_out.release()
