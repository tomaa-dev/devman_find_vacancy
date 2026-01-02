import requests
import pprint
import os
from terminaltables import AsciiTable
from dotenv import load_dotenv


def get_the_expected_salary(salary_from, salary_to, has_from, has_to):
    if not has_to and has_from:
        return int(salary_from * 1.2)
    elif not has_from and has_to:
        return int(salary_to * 0.8) 
    elif has_from and has_to:
        return int((salary_from + salary_to) / 2)
    return None


def predict_rub_salary_hh(hh_vacancies):
    if not hh_vacancies or hh_vacancies.get('currency') != 'RUR':
        return None

    salary_from = hh_vacancies.get('from')
    salary_to = hh_vacancies.get('to')
    has_from = salary_from is not None
    has_to = salary_to is not None

    return get_the_expected_salary(salary_from, salary_to, has_from, has_to)


def get_hh_statistics(popular_languages):
    hh_url = 'https://api.hh.ru/vacancies/'
    hh_vacancies = dict()

    for language in popular_languages:
        salaries = []
        page = 0
        pages_number = 1
        per_page = 100
        area = 1
        date_from = '2025-10-27'

        while page < pages_number:
            params = {
                'text': f'программист {language}',
                'area': area,
                'date_from': date_from,
                'per_page': per_page,
                'page': page
            }

            response = requests.get(hh_url, params=params)
            response.raise_for_status()
            hh_vacancies_page = response.json()
            hh_vacancies_count = hh_vacancies_page.get('found')

            for item in hh_vacancies_page.get("items", []):
                vacancy_salary = item.get('salary')
                predicted = predict_rub_salary_hh(vacancy_salary)
                if predicted:
                    salaries.append(predicted)

            pages_number = hh_vacancies_page.get('pages')
            page += 1

        processed = len(salaries)
        avg_salary = int(sum(salaries) / processed) if processed else 0

        hh_vacancies[language] = {
            "vacancies_found": hh_vacancies_count,
            "vacancies_processed": processed,
            "average_salary": avg_salary
        }

    return hh_vacancies


def predict_rub_salary_for_sj(sj_vacancies):
    payment_from = sj_vacancies.get('payment_from')
    payment_to = sj_vacancies.get('payment_to')
    currency = sj_vacancies.get('currency')

    if currency != 'rub':
        return None
    has_from = payment_from not in (None, 0)
    has_to = payment_to not in (None, 0)

    return get_the_expected_salary(payment_from, payment_to, has_from, has_to)


def get_sj_statistics(popular_languages, super_job_key):
    sj_url = 'https://api.superjob.ru/2.0/vacancies/'
    sj_vacancies = dict()
    perpage = 100

    for language in popular_languages:
        sj_salaries = []
        page = 0
        pages_number = 1
        town = 4

        while page < pages_number:
            params = {
                'keyword': language,
                'town': town,
                'count': perpage,
                'page': page
            }
            headers = {
                'X-Api-App-Id': super_job_key
            }

            response = requests.get(sj_url, headers=headers, params=params)
            response.raise_for_status()
            sj_vacancies_page = response.json()
            sj_vacancies_count = sj_vacancies_page.get('total')

            for item in sj_vacancies_page.get('objects', []):
                predicted = predict_rub_salary_for_sj(item)
                if predicted:
                    sj_salaries.append(predicted)
            pages_number = sj_vacancies_page.get('more')
            page += 1

        processed = len(sj_salaries)
        avg_salary = int(sum(sj_salaries) / processed) if processed else 0

        sj_vacancies[language] = {
            "vacancies_found": sj_vacancies_count,
            "vacancies_processed": processed,
            "average_salary": avg_salary
        }

    return sj_vacancies


def get_table(vacancies, title):
    table_data = [[
        'Язык программирования', 
        'Вакансий найдено', 
        'Вакансий обработано', 
        'Средняя зарплата'
    ]]

    for language, stats in vacancies.items():
        table_data.append([
            language,
            str(stats.get('vacancies_found')),
            str(stats.get('vacancies_processed')),
            str(stats.get('average_salary'))
        ])

    table_instance = AsciiTable(table_data, title)
    table_instance.justify_columns[2] = 'left'
    return table_instance.table


def main():
    load_dotenv()
    super_job_key = os.environ["SUPER_JOB_API_KEY"]

    popular_languages = [
        'Python', 
        'Java', 
        'JavaScript',
        'C',
        'C#', 
        'C++',
        'Go', 
        'Ruby', 
        '1c'
    ]

    hh_title = 'HeadHunter Moscow'
    sj_title = 'SuperJob Moscow'

    hh_stats = get_hh_statistics(popular_languages)
    sj_stats = get_sj_statistics(popular_languages, super_job_key)
    print(get_table(hh_stats, hh_title))
    print()
    print(get_table(sj_stats, sj_title))


if __name__ == '__main__':
    main()