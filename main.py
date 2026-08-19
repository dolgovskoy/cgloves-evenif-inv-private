import requests
import time

# Сайт, откуда берём список всех перчаток
GLOVES_URL = "https://ariflan159.github.io/cgloves-web/gloves.json"

# Roblox API через RoProxy
USERS_URL = "https://users.roproxy.com/v1/usernames/users"
INVENTORY_URL = "https://inventory.roproxy.com/v1/users/{}/items/2/{}/is-owned"


def get_gloves():
    response = requests.get(GLOVES_URL)

    print("gloves.json status:", response.status_code)

    response.raise_for_status()

    return response.json()


def get_user_id(username):
    data = {
        "usernames": [username],
        "excludeBannedUsers": True
    }

    response = requests.post(USERS_URL, json=data)

    print("Username API status:", response.status_code)

    response.raise_for_status()

    result = response.json()

    if not result.get("data"):
        return None

    return result["data"][0]["id"]


def check_glove(user_id, glove_id):
    url = INVENTORY_URL.format(user_id, glove_id)

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response.json()


def main():
    username = input("Введите Roblox username: ")

    print("\nПолучаю список перчаток...")

    gloves = get_gloves()

    print(f"Всего перчаток: {len(gloves)}")

    print("\nИщу пользователя...")

    user_id = get_user_id(username)

    if user_id is None:
        print("Пользователь не найден.")
        return

    print(f"User ID: {user_id}")

    obtained = []
    unobtained = []
    errors = []

    print("\nПроверяю перчатки...\n")

    for number, (glove_id, glove_name) in enumerate(gloves.items(), start=1):

        status = check_glove(user_id, glove_id)

        if status is True:
            obtained.append(glove_name)
            print(f"[{number}/{len(gloves)}] ✓ {glove_name}")

        elif status is False:
            unobtained.append(glove_name)
            print(f"[{number}/{len(gloves)}] ✗ {glove_name}")

        else:
            errors.append(glove_name)
            print(f"[{number}/{len(gloves)}] ? {glove_name} — ERROR")

        # Небольшая пауза между запросами
        time.sleep(0.5)

    print("\n" + "=" * 40)
    print("РЕЗУЛЬТАТ")
    print("=" * 40)

    print(f"\nПолучено: {len(obtained)}")
    for glove in obtained:
        print(f"  ✓ {glove}")

    print(f"\nНе получено: {len(unobtained)}")
    for glove in unobtained:
        print(f"  ✗ {glove}")

    if errors:
        print(f"\nОшибок: {len(errors)}")
        for glove in errors:
            print(f"  ? {glove}")


main()
