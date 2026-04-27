"""Tests for anim.storage."""

from pathlib import Path

import pytest

from anim.storage import Storage


@pytest.fixture
def temp_storage(tmp_path):
    """Storage instance using a temporary directory."""
    return Storage(tmp_path)


def test_save_and_list_audio(temp_storage):
    """Saving WAV bytes registers in index and list_audio."""
    wav = b"RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00" + b"\x00" * 16
    sid = temp_storage.save_audio(
        wav,
        title="My Narration",
        script_preview="First 200 chars...",
        voice="Kore",
    )
    assert sid
    assert (temp_storage.audio_dir / f"{sid}.wav").exists()
    listed = temp_storage.list_audio()
    assert len(listed) == 1
    assert listed[0]["title"] == "My Narration"
    assert listed[0]["voice"] == "Kore"
    assert "created_at" in listed[0]


def test_save_and_list_animation(temp_storage):
    """Saving a video file copies it and registers in index."""
    src = temp_storage.media_root / "source.mp4"
    src.write_bytes(b"fake mp4 content")
    aid = temp_storage.save_animation(src, title="My Video", job_id="job-1")
    assert aid
    dest = temp_storage.animations_dir / f"{aid}.mp4"
    assert dest.exists()
    assert dest.read_bytes() == b"fake mp4 content"
    listed = temp_storage.list_animations()
    assert len(listed) == 1
    assert listed[0]["title"] == "My Video"
    assert listed[0]["job_id"] == "job-1"


def test_get_paths(temp_storage):
    """get_animation_path and get_audio_path return Path or None."""
    wav = b"RIFF\x00\x00\x00\x00WAVE\x00\x00"
    sid = temp_storage.save_audio(wav, title="A")
    assert temp_storage.get_audio_path(sid) == temp_storage.audio_dir / f"{sid}.wav"
    assert temp_storage.get_audio_path("nonexistent") is None

    src = temp_storage.media_root / "v.mp4"
    src.write_bytes(b"x")
    aid = temp_storage.save_animation(src, title="V")
    assert temp_storage.get_animation_path(aid) == temp_storage.animations_dir / f"{aid}.mp4"
    assert temp_storage.get_animation_path("nonexistent") is None


def test_delete_animation(temp_storage):
    """delete_animation removes file and index entry."""
    src = temp_storage.media_root / "x.mp4"
    src.write_bytes(b"x")
    aid = temp_storage.save_animation(src, title="X")
    assert temp_storage.delete_animation(aid) is True
    assert not (temp_storage.animations_dir / f"{aid}.mp4").exists()
    assert temp_storage.list_animations() == []
    assert temp_storage.delete_animation(aid) is False


def test_delete_audio(temp_storage):
    """delete_audio removes file and index entry."""
    sid = temp_storage.save_audio(b"RIFF\x00\x00\x00\x00WAVE\x00", title="Y")
    assert temp_storage.delete_audio(sid) is True
    assert not (temp_storage.audio_dir / f"{sid}.wav").exists()
    assert temp_storage.list_audio() == []
    assert temp_storage.delete_audio(sid) is False


def test_save_animation_nonexistent_raises(temp_storage):
    """save_animation raises FileNotFoundError if source does not exist."""
    with pytest.raises(FileNotFoundError):
        temp_storage.save_animation(Path("/nonexistent/video.mp4"), title="T")
