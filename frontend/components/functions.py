from io import StringIO
from pathlib import Path
from typing import Optional
from zipfile import ZipFile

import requests
import streamlit as st

from .prompt_enum import PromptKeys


def set_session_state_variables() -> None:
    for key in PromptKeys:
        value = key.value
        if value not in st.session_state:
            st.session_state[value] = ""
    if "build_index_name" not in st.session_state:
        st.session_state["build_index_name"] = ""


def update_session_state_prompt_vars(
    summarize: Optional[str] = None,
    entity_extract: Optional[str] = None,
    community: Optional[str] = None,
    initial_setting: bool = False,
    prompt_dir: str = "./prompts",
) -> None:
    if initial_setting:
        summarize, entity_extract, community = get_prompts(prompt_dir)
    st.session_state[PromptKeys.SUMMARY.value] = summarize
    st.session_state[PromptKeys.ENTITY.value] = entity_extract
    st.session_state[PromptKeys.COMMUNITY.value] = community


# Function to call the REST API and return storage data
def get_storage_container_names(api_url: str, headers: dict) -> dict | None:
    """
    GET request to GraphRAG API for Azure Blob Storage Container names.
    """
    try:
        response = requests.get(f"{api_url}/data", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


# Function to call the REST API and return existing entity config
def get_entity_data(api_url: str, headers: dict) -> dict | None:
    try:
        response = requests.get(f"{api_url}/index/config/entity", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


# Function to call the REST API and return existing entity config
@st.cache_data
def get_indexes_data(api_url: str, headers: dict) -> dict | None:
    """
    GET request to GraphRAG API for existing indexes.
    """
    try:
        response = requests.get(f"{api_url}/index", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def build_index(
    api_url: str,
    headers: dict,
    storage_name: str,
    index_name: str,
    entity_extraction_prompt_filepath: str | StringIO = None,
    community_prompt_filepath: str | StringIO = None,
    summarize_description_prompt_filepath: str | StringIO = None,
) -> requests.Response:
    """Create a search index.
    This function kicks off a job that builds a knowledge graph (KG) index from files located in a blob storage container.
    """
    url = api_url + "/index"
    prompt_files = dict()
    if entity_extraction_prompt_filepath:
        prompt_files["entity_extraction_prompt"] = (
            open(entity_extraction_prompt_filepath, "r")
            if isinstance(entity_extraction_prompt_filepath, str)
            else entity_extraction_prompt_filepath
        )
    if community_prompt_filepath:
        prompt_files["community_report_prompt"] = (
            open(community_prompt_filepath, "r")
            if isinstance(community_prompt_filepath, str)
            else community_prompt_filepath
        )
    if summarize_description_prompt_filepath:
        prompt_files["summarize_descriptions_prompt"] = (
            open(summarize_description_prompt_filepath, "r")
            if isinstance(summarize_description_prompt_filepath, str)
            else summarize_description_prompt_filepath
        )
    return requests.post(
        url,
        files=prompt_files if len(prompt_files) > 0 else None,
        params={"index_name": index_name, "storage_name": storage_name},
        headers=headers,
    )


async def query_index(
    index_name: list[str], query_type: str, query: str, api_url: str, headers: dict
):
    try:
        request = {
            "index_name": index_name,
            "query": query,
            "reformat_context_data": True,
        }
        response = requests.post(
            f"{api_url}/query/{query_type.lower()}", headers=headers, json=request
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code} {response.json()}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def get_source_entity(
    index_name: str, entity_id: str, api_url: str, headers: dict
) -> dict | None:
    try:
        response = requests.get(
            f"{api_url}/source/entity/{index_name}/{entity_id}", headers=headers
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code} {response.json()}")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def show_index_options(indexes: dict) -> list[str]:
    options_indexes = [""]
    try:
        options_indexes = options_indexes + indexes["index_name"]
    except Exception as e:
        print(f"No indexes found, continuing...\nException: {str(e)}")
    return options_indexes


def _generate_prompts(
    api_url: str,
    headers: dict,
    storage_name: str,
    zip_file_name: str = "prompts.zip",
    limit: int = 5,
) -> None:
    """
    Generate graphrag prompts using data provided in a specific storage container.
    """
    url = api_url + "/index/config/prompts"
    params = {"storage_name": storage_name, "limit": limit}
    with requests.get(url, params=params, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(zip_file_name, "wb") as f:
            for chunk in r.iter_content():
                f.write(chunk)


def _extract_prompts_from_zip(zip_file_name: str = "prompts.zip"):
    with ZipFile(zip_file_name, "r") as zip_ref:
        zip_ref.extractall()


def generate_and_extract_prompts(
    api_url: str,
    headers: str,
    storage_name: str,
    zip_file_name: str = "prompts.zip",
    limit: int = 5,
) -> None:
    _generate_prompts(api_url, headers, storage_name, zip_file_name, limit)
    _extract_prompts_from_zip(zip_file_name)


def open_file(file_path: str | Path):
    with open(file_path, "r") as file:
        text = file.read()
    return text


def get_prompts(prompt_dir: str = "./prompts"):
    """
    Extract text from generated prompts.  Assumes file names comply with pregenerated file name standards.
    """
    prompt_paths = [
        prompt for prompt in Path(prompt_dir).iterdir() if prompt.name.endswith(".txt")
    ]
    summ_prompt = [
        open_file(path) for path in prompt_paths if path.name.startswith("summ")
    ][0]
    entity_ext_prompt = [
        open_file(path) for path in prompt_paths if path.name.startswith("entity")
    ][0]
    comm_report_prompt = [
        open_file(path) for path in prompt_paths if path.name.startswith("community")
    ][0]
    return summ_prompt, entity_ext_prompt, comm_report_prompt
