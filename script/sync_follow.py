import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)
GITHUB_NAME = os.getenv("GITHUB_NAME", None)
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def fetch_followers():
    url = f"https://api.github.com/users/{GITHUB_NAME}/followers"
    followers = []
    page = 1
    while True:
        res = requests.get(f"{url}?per_page=100&page={page}", headers=HEADERS)
        data = res.json()
        if not data:
            break
        followers.extend(user["login"] for user in data)
        page += 1

    print(f"Total followers: {len(followers)}")
    return followers


def fetch_following():
    url = "https://api.github.com/user/following"
    users, others = [], []
    page = 1
    while True:
        res = requests.get(f"{url}?per_page=100&page={page}", headers=HEADERS)
        data = res.json()
        if not data:
            break
        users.extend(user["login"] for user in data if user.get("type") == "User")
        others.extend(user["login"] for user in data if user.get("type") != "User")
        page += 1
        
    print(f"Total following users: {len(users)}")
    print(f"Total following organizations: {len(others)}")
    print(f"Followed organization: {'\nFollowed organization: '.join(others)}")
    return users


def follow(target_username: str):
    res = requests.put(
        f"https://api.github.com/user/following/{target_username}",
        headers={**HEADERS, "Content-Length": "0"},
    )
    if res.status_code == 204:
        print(f"Followed user: {target_username}")
    else:
        print(f"Failed to follow: {target_username} (Status: {res.status_code})")


def unfollow(target_username: str):
    url = f"https://api.github.com/user/following/{target_username}"
    res = requests.delete(url, headers=HEADERS)
    if res.status_code == 204:
        print(f"Unfollowed user: {target_username}")
    else:
        print(f"Failed to unfollow: {target_username} (Status: {res.status_code})")


def main():
    followers = set(fetch_followers())
    following = set(fetch_following())

    for user in followers:
        follow(user)

    to_unfollow = list(following - followers)
    for username in to_unfollow:
        unfollow(username)


if __name__ == "__main__":
    main()
