"""Load Python code files from a directory."""
import os
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader


class CodeLoader:
    """Load Python files from a directory."""

    def __init__(self, directory_path: str, file_extensions: List[str] = None):
        """
        Initialize the code loader.

        Args:
            directory_path: Path to the directory containing code files
            file_extensions: List of file extensions to load (default: ['.py'])
        """
        self.directory_path = Path(directory_path)
        self.file_extensions = file_extensions or ['.py']

        if not self.directory_path.exists():
            raise ValueError(f"Directory does not exist: {directory_path}")
        if not self.directory_path.is_dir():
            raise ValueError(f"Path is not a directory: {directory_path}")

    def load_documents(self) -> List[Document]:
        """
        Load all code files from the directory.

        Returns:
            List of Document objects with code content and metadata
        """
        all_documents = []

        for ext in self.file_extensions:
            # Use glob pattern to match files with the extension
            glob_pattern = f"**/*{ext}"

            try:
                loader = DirectoryLoader(
                    str(self.directory_path),
                    glob=glob_pattern,
                    loader_cls=TextLoader,
                    loader_kwargs={'autodetect_encoding': True},
                    show_progress=True,
                    use_multithreading=True
                )

                documents = loader.load()

                # Enrich metadata
                for doc in documents:
                    # Add file extension to metadata
                    doc.metadata['file_extension'] = ext
                    # Add relative path
                    full_path = Path(doc.metadata.get('source', ''))
                    try:
                        rel_path = full_path.relative_to(self.directory_path)
                        doc.metadata['relative_path'] = str(rel_path)
                    except ValueError:
                        doc.metadata['relative_path'] = str(full_path)

                all_documents.extend(documents)

            except Exception as e:
                print(f"Warning: Error loading {ext} files: {e}")
                continue

        return all_documents

    def get_stats(self, documents: List[Document]) -> dict:
        """
        Get statistics about loaded documents.

        Args:
            documents: List of loaded documents

        Returns:
            Dictionary with statistics
        """
        total_chars = sum(len(doc.page_content) for doc in documents)

        files_by_ext = {}
        for doc in documents:
            ext = doc.metadata.get('file_extension', 'unknown')
            files_by_ext[ext] = files_by_ext.get(ext, 0) + 1

        return {
            'total_files': len(documents),
            'total_characters': total_chars,
            'files_by_extension': files_by_ext,
            'average_file_size': total_chars // len(documents) if documents else 0
        }
