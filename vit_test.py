import requests
from PIL import Image, ImageDraw, ImageFont
import torch
import cv2
import numpy as np

from transformers import OwlViTProcessor, OwlViTForObjectDetection

processor = OwlViTProcessor.from_pretrained("google/owlvit-base-patch32")
model = OwlViTForObjectDetection.from_pretrained("google/owlvit-base-patch32")


font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"  # 例としてArialフォント
font = ImageFont.truetype(font_path, 30)

def predict(image: Image):
    texts = [["a photo of a dish"]]
    inputs = processor(text=texts, images=image, return_tensors="pt")
    outputs = model(**inputs)
    target_sizes = torch.Tensor([image.size[::-1]])
    # Convert outputs (bounding boxes and class logits) to COCO API
    results = processor.post_process_object_detection(outputs=outputs, target_sizes=target_sizes, threshold=0.1)
    i = 0  # Retrieve predictions for the first image for the corresponding text queries
    text = texts[i]
    boxes, scores, labels = results[i]["boxes"], results[i]["scores"], results[i]["labels"]
    return [{"box": box, "score": score.item(), "label": text[label]} for box, score, label in zip(boxes, scores, labels)]

def write_box_on_image(image:Image, boxes):
    for box_info in boxes:
        draw = ImageDraw.Draw(image)
        rectangle_position = tuple(box_info["box"])
        # 四角を描く
        text_position = (rectangle_position[0], rectangle_position[1])
        text_content = f'{round(box_info["score"], 3)}, {box_info["label"]}'

        # テキストを画像に書き込む
        draw.text(text_position, text_content, font=font, fill="green")
        draw.rectangle(rectangle_position, outline="green", width=5)
        print(f"Detected {box_info['label']} with confidence {round(box_info['score'], 3)} at location {rectangle_position}")

# 入力と出力の動画ファイルのパスを指定します
input_video_path = 'food-detection.mp4'
output_video_path = 'food-detection-output.mp4'

# 動画を読み込む
cap = cv2.VideoCapture(input_video_path)
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

# 動画の情報を取得
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = int(cap.get(cv2.CAP_PROP_FPS))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec

# 新しい動画ファイルを書き込むためのオブジェクトを作成
out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # OpenCVの画像をPillowのImageに変換
    img_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    boxes = predict(img_pil)
    write_box_on_image(img_pil, boxes)
    # PillowのImageをOpenCVの画像に戻す
    frame = cv2.cvtColor(np.array(img_pil, dtype=np.uint8), cv2.COLOR_RGB2BGR)

    # フレームを出力動画に書き込む
    out.write(frame)

# リソースの解放
cap.release()
out.release()