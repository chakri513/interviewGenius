import json
from typing import List

import cv2
import numpy as np
import mediapipe as mp
import speech_recognition as sr
from deepface import DeepFace
from fastapi import HTTPException
from textblob import TextBlob
import librosa
import soundfile as sf

from app.src.db.models import Interview


class InterviewAnalyzer:
    def __init__(self):
        # Initialize MediaPipe pose estimation
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            min_detection_confidence=0.5
        )

        # Speech recognition and analysis
        self.recognizer = sr.Recognizer()

    def analyze_emotion(self, frame):
        """
        Perform emotion recognition using DeepFace

        Args:
            frame (numpy.ndarray): RGB video frame

        Returns:
            dict: Emotion analysis results
        """
        try:
            emotion_result = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False
            )[0]['emotion']

            dominant_emotion = max(emotion_result, key=emotion_result.get)

            return {
                'dominant_emotion': dominant_emotion,
                'emotion_probabilities': emotion_result
            }
        except Exception as e:
            return {'error': str(e)}

    def estimate_pose(self, frame):
        """
        Estimate body pose and confidence indicators

        Args:
            frame (numpy.ndarray): RGB video frame

        Returns:
            dict: Pose estimation results
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)

        if not results.pose_landmarks:
            return {'pose_detected': False}

        landmarks = results.pose_landmarks.landmark

        # Calculate shoulder angle
        left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]

        shoulder_angle = np.abs(
            np.arctan2(
                right_shoulder.y - left_shoulder.y,
                right_shoulder.x - left_shoulder.x
            ) * 180 / np.pi
        )

        return {
            'pose_detected': True,
            'shoulder_angle': shoulder_angle,
            'posture_confidence': 1 - abs(shoulder_angle - 180) / 180
        }

    def analyze_speech(self, audio_file):
        """
        Perform speech-to-text and linguistic analysis

        Args:
            audio_file (str): Path to audio file

        Returns:
            dict: Speech analysis results
        """
        # Speech recognition
        import speech_recognition as sr
        with sr.AudioFile(audio_file) as source:
            audio = self.recognizer.record(source)

        try:
            text = self.recognizer.recognize_ibm(audio)
        except sr.UnknownValueError:
            return {'error': 'Speech could not be understood'}
        except sr.RequestError:
            return {'error': 'Could not request results'}

        # Sentiment analysis
        sentiment = TextBlob(text).sentiment

        # Speech characteristics
        y, sr = librosa.load(audio_file)
        speech_rate = len(text.split()) / (len(y) / sr)
        pitch = librosa.yin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))

        return {
            'transcription': text,
            'sentiment_polarity': sentiment.polarity,
            'sentiment_subjectivity': sentiment.subjectivity,
            'speech_rate': speech_rate,
            'average_pitch': np.mean(pitch)
        }

    def comprehensive_analysis(self, video_frames, audio_file):
        """
        Combine emotion, pose, and speech analysis

        Args:
            video_frames (list): List of video frames
            audio_file (str): Path to audio file

        Returns:
            dict: Comprehensive behavioral insights
        """
        results = {
            'emotion_analysis': [],
            'pose_analysis': [],
            'speech_analysis': {}
        }

        # Emotion analysis for each frame
        for frame in video_frames:
            results['emotion_analysis'].append(
                self.analyze_emotion(frame)
            )

        # Pose analysis for first and last frames
        if video_frames:
            results['pose_analysis'] = [
                self.estimate_pose(video_frames[0]),
                self.estimate_pose(video_frames[-1])
            ]

        # Speech analysis
        results['speech_analysis'] = self.analyze_speech(audio_file)

        return results


# Optional Gemini integration for deeper insights
def generate_behavioral_insights(analysis_results):
    """
    Use Gemini to generate deeper behavioral insights

    Args:
        analysis_results (dict): Comprehensive analysis results

    Returns:
        str: Generated behavioral insights
    """
    import google.generativeai as genai

    # Configure Gemini (ensure API key is securely managed)
    genai.configure(api_key='YOUR_GEMINI_API_KEY')
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Analyze the following interview behavioral data:
    {analysis_results}

    Provide a comprehensive interpretation focusing on:
    1. Emotional stability and composure
    2. Communication effectiveness
    3. Confidence indicators
    4. Potential areas of improvement
    """

    response = model.generate_content(prompt)
    return response.text


# Example usage
def process_interview_recording(video_path, audio_path):
    analyzer = InterviewAnalyzer()

    # Load video frames
    cap = cv2.VideoCapture(video_path)
    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()

    # Perform comprehensive analysis
    analysis_results = analyzer.comprehensive_analysis(frames, audio_path)

    # Optional: Generate deeper insights with Gemini
    behavioral_insights = generate_behavioral_insights(analysis_results)

    return analysis_results, behavioral_insights


async def process_audio_to_text(recording_path: str) -> str:
    """
    Process audio file and convert to text using speech recognition
    """
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(recording_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_tensorflow(audio)
            return text
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process audio: {str(e)}"
        )


async def prepare_feedback_data(interview: Interview, recordings_text: List[str]) -> str:
    """
    Prepare the question-answer pairs for Gemini feedback
    """
    qa_pairs = []
    for question, answer_text in zip(interview.questions, recordings_text):
        qa_pairs.append({
            "question": question["text"],
            "answer": answer_text,
            "category": question["category"],
            "rubric": question["rubric"]
        })

    return json.dumps(qa_pairs)