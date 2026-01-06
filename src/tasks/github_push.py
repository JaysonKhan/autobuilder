"""GitHub push utility"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GitHubPusher:
    """Push code changes to GitHub"""
    
    def __init__(self, config: dict):
        self.config = config
        self.ssh_key_path = config.get('github', {}).get('ssh_key_path', '/root/.ssh/autobuilder_github')
        self.repo_url = config.get('github', {}).get('repo_url', '')
        self.repo_path = Path(config.get('github', {}).get('repo_path', '/opt/autobuilder/repo'))
        self.branch = config.get('github', {}).get('branch', 'myself')
        self.git_user_name = config.get('github', {}).get('git_user_name', 'AutoBuilder Bot')
        self.git_user_email = config.get('github', {}).get('git_user_email', 'bot@jaysonkhan.com')
    
    def push_changes(
        self,
        source_dir: str,
        job_id: str,
        commit_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Push changes from source_dir to GitHub
        
        Args:
            source_dir: Directory containing code to push
            job_id: Job ID for commit message
            commit_message: Optional custom commit message
        
        Returns:
            Dict with success status and message
        """
        try:
            # Ensure repo is cloned
            if not self.repo_path.exists():
                self._clone_repo()
            
            # Setup git config
            self._setup_git_config()
            
            # Copy files to repo
            self._copy_files(source_dir, self.repo_path)
            
            # Commit and push
            commit_msg = commit_message or f"[{job_id}] Auto-generated code"
            self._commit_and_push(commit_msg)
            
            return {
                'success': True,
                'message': f"Successfully pushed to {self.branch} branch",
                'commit_message': commit_msg
            }
            
        except Exception as e:
            logger.error(f"GitHub push failed: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def _clone_repo(self):
        """Clone repository if not exists"""
        if not self.repo_url:
            raise ValueError("GitHub repo_url not configured")
        
        self.repo_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use SSH key for git operations
        env = os.environ.copy()
        env['GIT_SSH_COMMAND'] = f'ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no'
        
        subprocess.run(
            ['git', 'clone', self.repo_url, str(self.repo_path)],
            env=env,
            check=True,
            timeout=300
        )
    
    def _setup_git_config(self):
        """Setup git user name and email"""
        env = os.environ.copy()
        env['GIT_SSH_COMMAND'] = f'ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no'
        
        subprocess.run(
            ['git', 'config', 'user.name', self.git_user_name],
            cwd=self.repo_path,
            env=env,
            check=True
        )
        
        subprocess.run(
            ['git', 'config', 'user.email', self.git_user_email],
            cwd=self.repo_path,
            env=env,
            check=True
        )
    
    def _copy_files(self, source_dir: str, target_dir: Path):
        """Copy files from source to target"""
        import shutil
        
        source_path = Path(source_dir)
        
        # Copy all files except .git
        for item in source_path.iterdir():
            if item.name == '.git':
                continue
            
            target_item = target_dir / item.name
            if item.is_dir():
                if target_item.exists():
                    shutil.rmtree(target_item)
                shutil.copytree(item, target_item)
            else:
                shutil.copy2(item, target_item)
    
    def _commit_and_push(self, commit_message: str):
        """Commit changes and push to GitHub"""
        env = os.environ.copy()
        env['GIT_SSH_COMMAND'] = f'ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no'
        
        # Check if branch exists
        result = subprocess.run(
            ['git', 'branch', '-a'],
            cwd=self.repo_path,
            env=env,
            capture_output=True,
            text=True
        )
        
        branch_exists = self.branch in result.stdout or f'origin/{self.branch}' in result.stdout
        
        # Checkout or create branch
        if not branch_exists:
            subprocess.run(
                ['git', 'checkout', '-b', self.branch],
                cwd=self.repo_path,
                env=env,
                check=True
            )
        else:
            subprocess.run(
                ['git', 'checkout', self.branch],
                cwd=self.repo_path,
                env=env,
                check=True
            )
        
        # Add all changes
        subprocess.run(
            ['git', 'add', '-A'],
            cwd=self.repo_path,
            env=env,
            check=True
        )
        
        # Commit
        subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=self.repo_path,
            env=env,
            check=True
        )
        
        # Push
        subprocess.run(
            ['git', 'push', 'origin', self.branch],
            cwd=self.repo_path,
            env=env,
            check=True,
            timeout=300
        )

