import os
import lxml.html
import re
import requests
import tempfile
import Levenshtein


class Registrars:
    '''
        https://www.icann.org/registrar-reports/accredited-list.html
    '''
    registrars = []
    registrars_file_path = os.path.join(tempfile.gettempdir(), 'registrars_names')

    @classmethod
    def get_registrar(
        cls,
        subject,
    ):
        cls.check_and_update_registrars()

        edited_subject = re.sub(
            pattern=r'[^\d\w]',
            repl='',
            string=subject,
        )
        edited_subject = edited_subject.lower()

        for registrar in cls.registrars:
            if edited_subject in registrar['edited'].lower():
                return registrar['original']

        most_close_registrar = ''
        most_close_registrar_distance_ratio = 0
        for registrar in cls.registrars:
            registrar_distance_ratio = Levenshtein.ratio(
                edited_subject,
                registrar['edited'],
            )
            if registrar_distance_ratio > most_close_registrar_distance_ratio:
                most_close_registrar = registrar['original']
                most_close_registrar_distance_ratio = registrar_distance_ratio

        return most_close_registrar

    @classmethod
    def check_and_update_registrars(
        cls,
    ):
        if not os.path.exists(cls.registrars_file_path):
            cls.download_registrars_file()

        if not cls.registrars:
            cls.update_registrars()

    @classmethod
    def update_registrars(
        cls,
    ):
        with open(cls.registrars_file_path) as registrars_names_file:
            original_names = registrars_names_file.readlines()

        cls.registrars = [
            registrar
            for registrar in [
                {
                    'original': original_name.strip(),
                    'edited': re.sub(
                        pattern=r'[^\d\w]',
                        repl='',
                        string=original_name,
                    ).lower(),
                }
                for original_name in original_names
            ]
            if len(registrar['edited']) > 4
        ]

    @classmethod
    def download_registrars_file(
        cls,
    ):
        response = requests.get(
            url='https://www.icann.org/registrar-reports/accredited-list.html',
        )

        nodes_tree = lxml.html.fromstring(
            html=response.text,
        )
        anchor_elements = nodes_tree.cssselect(
            expr='table > tr > td > a',
        )

        with open(cls.registrars_file_path, 'w') as registrars_files:
            for anchor in anchor_elements:
                registrars_files.write(
                    '{registrar_name}\n'.format(
                        registrar_name=str(anchor.text_content()),
                    )
                )
