from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer, QMediaPlaylist
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class VideoPlayer(QWidget):
    def __init__(self, video_filepath: str):
        super().__init__()
        self.video_widget = QVideoWidget()
        self.layout = QVBoxLayout()
        self.playlist = QMediaPlaylist(self)
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        self.layout.addWidget(self.video_widget)
        self.setLayout(self.layout)

        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(video_filepath)))
        self.playlist.setPlaybackMode(QMediaPlaylist.Loop)

        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(video_filepath)))
        self.mediaPlayer.setVideoOutput(self.video_widget)
        self.mediaPlayer.setPlaylist(self.playlist)

        self.mediaPlayer.play()
