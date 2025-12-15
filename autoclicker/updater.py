"""
GitHub 기반 자동 업데이트 모듈
"""
import os
import sys
import json
import subprocess
import threading
from typing import Optional, Dict, Tuple

try:
    import requests
except ImportError:
    requests = None

try:
    from packaging import version as pkg_version
except ImportError:
    pkg_version = None

from autoclicker.version import __version__
from autoclicker.config import load_config, save_config


def _compare_versions(v1: str, v2: str) -> int:
    """
    버전 비교 함수
    Returns: v1 > v2면 1, v1 == v2면 0, v1 < v2면 -1
    """
    if pkg_version:
        try:
            v1_parsed = pkg_version.parse(v1)
            v2_parsed = pkg_version.parse(v2)
            if v1_parsed > v2_parsed:
                return 1
            elif v1_parsed == v2_parsed:
                return 0
            else:
                return -1
        except:
            pass
    
    # 간단한 버전 비교 (packaging이 없을 경우)
    def parse_version(v):
        parts = []
        for part in v.replace("v", "").split("."):
            try:
                parts.append(int(part))
            except:
                parts.append(0)
        return parts
    
    v1_parts = parse_version(v1)
    v2_parts = parse_version(v2)
    
    max_len = max(len(v1_parts), len(v2_parts))
    v1_parts.extend([0] * (max_len - len(v1_parts)))
    v2_parts.extend([0] * (max_len - len(v2_parts)))
    
    for i in range(max_len):
        if v1_parts[i] > v2_parts[i]:
            return 1
        elif v1_parts[i] < v2_parts[i]:
            return -1
    
    return 0


class Updater:
    """GitHub Releases API를 사용한 업데이트 관리자"""
    
    def __init__(self):
        self.config = load_config()
        self.current_version = __version__
        # GitHub 저장소 정보 (username/repo 형식)
        self.repo = self.config.get("github_repo", "")  # 예: "username/repo-name"
        self.latest_version: Optional[str] = None
        self.latest_release: Optional[Dict] = None
        
    def check_update(self, timeout: int = 5) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        최신 버전 확인
        
        Returns:
            (업데이트 있음, 최신 버전, 릴리즈 노트) 튜플
        """
        if not requests:
            return False, None, "requests 라이브러리가 설치되지 않았습니다."
        
        if not self.repo:
            return False, None, "GitHub 저장소 정보가 설정되지 않았습니다."
        
        try:
            # GitHub Releases API 호출
            url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            response = requests.get(url, timeout=timeout)
            
            if response.status_code != 200:
                return False, None, f"업데이트 확인 실패: {response.status_code}"
            
            release_data = response.json()
            self.latest_release = release_data
            self.latest_version = release_data.get("tag_name", "").lstrip("v")
            
            # 버전 비교
            try:
                comparison = _compare_versions(self.latest_version, self.current_version)
                
                if comparison > 0:  # latest > current
                    release_notes = release_data.get("body", "업데이트 정보 없음")
                    return True, self.latest_version, release_notes
                else:
                    return False, self.current_version, "최신 버전입니다."
            except Exception as e:
                return False, None, f"버전 비교 오류: {e}"
                
        except requests.exceptions.Timeout:
            return False, None, "업데이트 확인 시간 초과"
        except requests.exceptions.RequestException as e:
            return False, None, f"업데이트 확인 실패: {e}"
        except Exception as e:
            return False, None, f"오류 발생: {e}"
    
    def download_update(self, download_path: Optional[str] = None) -> Tuple[bool, str]:
        """
        최신 버전 다운로드
        
        Args:
            download_path: 다운로드 경로 (None이면 현재 디렉토리)
            
        Returns:
            (성공 여부, 메시지) 튜플
        """
        if not self.latest_release:
            has_update, _, _ = self.check_update()
            if not has_update:
                return False, "다운로드할 업데이트가 없습니다."
        
        try:
            # Windows용 실행 파일 찾기 (.exe)
            assets = self.latest_release.get("assets", [])
            exe_asset = None
            
            for asset in assets:
                if asset.get("name", "").endswith(".exe"):
                    exe_asset = asset
                    break
            
            if not exe_asset:
                return False, "Windows용 실행 파일(.exe)을 찾을 수 없습니다."
            
            download_url = exe_asset.get("browser_download_url")
            if not download_url:
                return False, "다운로드 URL을 찾을 수 없습니다."
            
            # 다운로드 경로 설정
            if download_path is None:
                download_path = os.path.dirname(os.path.abspath(__file__))
            
            filename = exe_asset.get("name", f"update_{self.latest_version}.exe")
            filepath = os.path.join(download_path, filename)
            
            # 파일 다운로드
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
            
            return True, f"다운로드 완료: {filepath}"
            
        except Exception as e:
            return False, f"다운로드 실패: {e}"
    
    def install_update(self, installer_path: str) -> bool:
        """
        업데이트 설치 (실행 파일 실행)
        
        Args:
            installer_path: 설치 파일 경로
            
        Returns:
            성공 여부
        """
        try:
            if not os.path.exists(installer_path):
                return False
            
            # 백그라운드에서 설치 프로그램 실행
            subprocess.Popen([installer_path], shell=True)
            return True
        except Exception as e:
            print(f"설치 오류: {e}")
            return False
    
    def set_repo(self, repo: str):
        """GitHub 저장소 설정"""
        self.repo = repo
        self.config["github_repo"] = repo
        save_config(self.config)


def check_update_async(callback):
    """
    비동기로 업데이트 확인
    
    Args:
        callback: (has_update, latest_version, message) 인자를 받는 콜백 함수
    """
    def _check():
        updater = Updater()
        has_update, version, message = updater.check_update()
        callback(has_update, version, message)
    
    thread = threading.Thread(target=_check, daemon=True)
    thread.start()
