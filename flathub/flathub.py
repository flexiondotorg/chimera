import subprocess
from typing import List, Dict
import os
import flathub
import requests


class Flathub:

    def __init__(self):
        flathub_url = "https://dl.flathub.org/repo/flathub.flatpakrepo"
        self.__add_repo("flathub", flathub_url)
        self.__api_url = "https://flathub.org/api/v1/apps"
        self.__applications = self.__get_application_list()

    def __add_repo(self, name: str, url: str) -> None:
        if os.geteuid() == 0:
            command = ["flatpak", "remote-add", "--if-not-exists", name, url]
        else:
            command = ["flatpak", "remote-add", "--user", "--if-not-exists", name, url]
        # This only adds the flatpak repo if it isn't already installed
        return_value = subprocess.call(command)
        if return_value != 0:
            print("Error: Failed to add the {name} repo to with url {url} flatpak".format(name=name, url=url))

    def __get_application_list(self):
        applications = []
        api_response = requests.get(self.__api_url)
        if api_response.status_code == requests.codes.ok:
            installed_list = self.__get_installed_list()
            for entry in api_response.json():
                flatpak_id = entry['flatpakAppId']
                name = entry['name']
                description = entry['summary']
                image_url = entry['iconDesktopUrl']
                available_version = entry['currentReleaseVersion']
                installed = False
                version = ""

                for app in installed_list:
                    if app['flatpak_id'].strip() == flatpak_id:
                        installed = True
                        version = app['version']

                application = flathub.Application(flatpak_id, name, description, image_url, installed, version, available_version)
                applications.append(application)
        return applications

    def get_available_applications(self) -> List[flathub.Application]:
        applications = []
        for application in self.__applications:
            # Don't add if the whitelist is enabled and the app isn't in it
            if application.flatpak_id not in flathub.whitelist:
                continue
            if not application.installed or (application.installed and application.busy):
                applications.append(application)
        return applications

    def get_installed_applications(self) -> List[flathub.Application]:
        applications = []
        for application in self.__applications:
            if application.installed and application.flatpak_id in flathub.whitelist and not application.busy:
                applications.append(application)
        return applications

    def get_application(self, flatpak_id: str) -> flathub.Application:
        for application in self.__applications:
            if application.flatpak_id == flatpak_id:
                return application
        return None

    def __get_installed_list(self) -> List[Dict[str, any]]:
        if os.geteuid() == 0:
            command = ["flatpak", "list", "--app"]
        else:
            command = ["flatpak", "list", "--user", "--app"]
        installed_list = []
        for line in subprocess.check_output(command).splitlines():
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            try:
                _, flatpak_id, version, _ = line.split("\t", 3)
            except ValueError:
                flatpak_id = line
                version = ""
            application_tuple = {
                'flatpak_id': flatpak_id,
                'version': version
            }
            installed_list.append(application_tuple)
        return installed_list

    @staticmethod
    def install(flatpak_id: str) -> subprocess:
        if os.geteuid() == 0:
            command = ["flatpak", "install", "-y", "flathub", flatpak_id]
        else:
            command = ["flatpak", "install", "--user", "-y", "flathub", flatpak_id]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    @staticmethod
    def uninstall(flatpak_id: str) -> subprocess:
        if os.geteuid() == 0:
            command = ["flatpak", "uninstall", "-y", flatpak_id]
        else:
            command = ["flatpak", "uninstall", "--user", "-y", flatpak_id]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    @staticmethod
    def update(flatpak_id: str) -> subprocess:
        if os.geteuid() == 0:
            command = ["flatpak", "update", "-y", flatpak_id]
        else:
            command = ["flatpak", "update", "--user", "-y", flatpak_id]
        return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
