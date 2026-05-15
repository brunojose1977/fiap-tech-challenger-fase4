"""Orquestração: S3 -> YOLO predict -> S3 -> anotação violência -> S3."""

from __future__ import annotations

import logging
from pathlib import Path

import cv2
from ultralytics import YOLO

from yolo_violence_pipeline.config import PipelineConfig
from yolo_violence_pipeline.s3_io import download_file, s3_client, upload_file
from yolo_violence_pipeline.violence import is_violence_detected

logger = logging.getLogger(__name__)


def _find_latest_video(save_dir: Path) -> Path | None:
    for pattern in ("*.avi", "*.mp4"):
        found = list(save_dir.glob(pattern))
        if found:
            return max(found, key=lambda p: p.stat().st_mtime)
    return None


def run_pipeline(cfg: PipelineConfig) -> dict:
    """
    Executa o fluxo equivalente ao notebook Colab.

    Returns:
        Dicionário com caminhos e flags para observabilidade.
    """
    work = Path(cfg.work_dir)
    work.mkdir(parents=True, exist_ok=True)
    local_video = work / Path(cfg.s3_input_key).name

    client = s3_client(cfg.aws_region)
    download_file(client, cfg.s3_input_bucket, cfg.s3_input_key, local_video)

    if not local_video.is_file():
        msg = f"Vídeo de entrada não encontrado após download: {local_video}"
        raise FileNotFoundError(msg)

    model = YOLO(cfg.model_name)

    results = model.predict(
        source=str(local_video),
        task="pose",
        save=True,
        conf=cfg.predict_conf,
        iou=cfg.predict_iou,
        imgsz=cfg.predict_imgsz,
        stream=True,
        verbose=True,
    )

    out_path = None
    for r in results:
        out_path = getattr(r, "save_dir", None)

    if out_path:
        save_dir = Path(out_path)
        predict_video = _find_latest_video(save_dir)
        if predict_video and predict_video.is_file():
            upload_file(client, predict_video, cfg.s3_predict_bucket, predict_video.name)
        else:
            logger.warning("Nenhum vídeo .avi/.mp4 encontrado em %s", save_dir)

    output_video_dir = work / "runs" / "pose" / "custom_annotated_videos"
    output_video_dir.mkdir(parents=True, exist_ok=True)
    stem = cfg.model_name.replace(".pt", "")
    output_video_path = output_video_dir / f"video_violence_detected_{stem}.mp4"

    cap = cv2.VideoCapture(str(local_video))
    if not cap.isOpened():
        msg = f"Não foi possível abrir o vídeo: {local_video}"
        raise OSError(msg)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out_video = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))
    if not out_video.isOpened():
        msg = f"Não foi possível criar o writer: {output_video_path}"
        raise OSError(msg)

    detector_results = model.predict(
        source=str(local_video),
        task="pose",
        save=False,
        conf=cfg.predict_conf,
        iou=cfg.predict_iou,
        imgsz=cfg.predict_imgsz,
        stream=True,
        verbose=False,
    )

    violet_frames_count = 0
    violet_detected_in_any_frame = False
    for frame_idx, r in enumerate(detector_results):
        annotated_frame = r.plot()
        frame_violence_detected = False
        if r.keypoints is not None and len(r.keypoints) > 0:
            for person_kpts in r.keypoints:
                if is_violence_detected(
                    person_kpts, confidence_threshold=cfg.violence_confidence_threshold
                ):
                    frame_violence_detected = True
                    violet_detected_in_any_frame = True
                    break

        if frame_violence_detected:
            violet_frames_count += 1
            text = "Violence Detected!"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.5
            font_thickness = 3
            text_color = (0, 0, 255)
            text_bg_color = (0, 0, 0)
            (text_width, text_height), _baseline = cv2.getTextSize(
                text, font, font_scale, font_thickness
            )
            text_x = 20
            text_y = text_height + 20
            cv2.rectangle(
                annotated_frame,
                (text_x - 10, text_y - text_height - 10),
                (text_x + text_width + 10, text_y + 10),
                text_bg_color,
                -1,
            )
            cv2.putText(
                annotated_frame,
                text,
                (text_x, text_y),
                font,
                font_scale,
                text_color,
                font_thickness,
                cv2.LINE_AA,
            )
            logger.warning("Violence (placeholder) no frame %s", frame_idx + 1)

        out_video.write(annotated_frame)

    out_video.release()

    if output_video_path.is_file():
        upload_file(client, output_video_path, cfg.s3_output_bucket, output_video_path.name)
    else:
        logger.error("Arquivo de saída não gerado: %s", output_video_path)

    return {
        "local_input": str(local_video),
        "output_video": str(output_video_path),
        "violence_detected_any_frame": violet_detected_in_any_frame,
        "violence_frames": violet_frames_count,
    }
