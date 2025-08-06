import os
import requests
import time

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", None)
GITHUB_NAME = os.getenv("GITHUB_NAME", None)

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}
MAX_RETRIES = 5
WAIT = 1.5


def safe_request(url, headers, method):
    retries = 0
    while retries < MAX_RETRIES:
        response = method(url, headers=headers)
        if response.status_code == 403:
            print(f"Rate limit hit. Retrying after 30 seconds...")
            time.sleep(30)

            global WAIT
            WAIT += WAIT

            retries += 1
        elif response.status_code in [500, 502, 503]:
            print(
                f"Server error ({response.status_code}). Retrying after 10 seconds..."
            )
            time.sleep(10)
            retries += 1
        else:
            return response
    print(f"Failed after {MAX_RETRIES} retries.")
    return None


def fetch_followers():
    url = f"https://api.github.com/users/{GITHUB_NAME}/followers"
    followers = []
    page = 1

    while True:
        response = safe_request(
            f"{url}?per_page=100&page={page}", HEADERS, requests.get
        )
        if response.status_code != 200:
            print(f"Failed to fetch followers (Status: {response.status_code})")
            break

        data = response.json()
        if not data:
            break

        followers.extend(user["login"] for user in data)
        page += 1

    print(f"Total followers: {len(followers)}")
    return followers


def fetch_following():
    url = "https://api.github.com/user/following"
    user_accounts, organizations = [], []
    page = 1

    while True:
        response = safe_request(
            f"{url}?per_page=100&page={page}", HEADERS, requests.get
        )
        if response.status_code != 200:
            print(f"Failed to fetch following list (Status: {response.status_code})")
            break

        data = response.json()
        if not data:
            break

        user_accounts.extend(
            user["login"] for user in data if user.get("type") == "User"
        )
        organizations.extend(
            user["login"] for user in data if user.get("type") != "User"
        )
        page += 1

    print(f"Total following users: {len(user_accounts)}")
    print(f"Total following organizations: {len(organizations)}")
    return user_accounts


def fetch_starred_repositories():
    url = f"https://api.github.com/users/{GITHUB_NAME}/starred"
    starred_repos = {}
    page = 1

    while True:
        response = safe_request(
            f"{url}?per_page=100&page={page}", HEADERS, requests.get
        )
        if response.status_code != 200:
            print(
                f"Failed to fetch starred repositories (Status: {response.status_code})"
            )
            break

        data = response.json()
        if not data:
            break

        starred_repos.update(
            (repo["owner"]["login"], repo["name"])
            for repo in data
            if repo["owner"].get("type") == "User"
            and repo["owner"].get("login") != GITHUB_NAME
        )
        page += 1

    print(f"Total starred repositories: {len(starred_repos)}")
    return starred_repos


def fetch_top_repository(username: str):
    url = f"https://api.github.com/search/repositories?q=user:{username}&sort=stars&order=desc&per_page=1"
    response = safe_request(url, HEADERS, requests.get)

    if response.status_code != 200:
        print(
            f"    Failed to fetch top repository for {username} (Status: {response.status_code})"
        )
        return None

    data = response.json()
    if data.get("total_count", 0) == 0:
        print(f"    No repositories found for user: {username}")
        return None

    top_repo = data["items"][0]
    repo_name = top_repo["name"]
    stars = top_repo["stargazers_count"]

    print(f"    Top repository of {username}: {repo_name} ({stars})")
    if stars > 9:
        return repo_name

    return None


def follow_user(username: str):
    url = f"https://api.github.com/user/following/{username}"
    response = safe_request(url, {**HEADERS, "Content-Length": "0"}, requests.put)

    if response.status_code == 204:
        print(f"Followed user: {username}")
    else:
        print(f"Failed to follow user: {username} (Status: {response.status_code})")


def unfollow_user(username: str):
    url = f"https://api.github.com/user/following/{username}"
    response = safe_request(url, HEADERS, requests.delete)

    if response.status_code == 204:
        print(f"Unfollowed user: {username}")
    else:
        print(f"Failed to unfollow user: {username} (Status: {response.status_code})")


def star_repository(owner: str, repo_name: str):
    url = f"https://api.github.com/user/starred/{owner}/{repo_name}"
    response = safe_request(url, {**HEADERS, "Content-Length": "0"}, requests.put)

    if response.status_code == 204:
        print(f"    Starred repository: {owner}/{repo_name}")
    else:
        print(
            f"    Failed to star repository: {owner}/{repo_name} (Status: {response.status_code})"
        )


def unstar_repository(owner: str, repo_name: str):
    url = f"https://api.github.com/user/starred/{owner}/{repo_name}"
    response = safe_request(url, HEADERS, requests.delete)

    if response.status_code == 204:
        print(f"    Unstarred repository: {owner}/{repo_name}")
    else:
        print(
            f"    Failed to unstar repository: {owner}/{repo_name} (Status: {response.status_code})"
        )


def main():
    followers = set(fetch_followers())
    following = set(fetch_following())

    for user in followers:
        follow_user(user)
        repo_name = fetch_top_repository(user)
        if repo_name:
            star_repository(user, repo_name)
        time.sleep(WAIT)

    to_unfollow = list(following - followers)
    for username in to_unfollow:
        unfollow_user(username)

    stars = fetch_starred_repositories()
    for owner, repo_name in stars.items():
        if owner not in followers:
            unstar_repository(owner, repo_name)
            time.sleep(WAIT)


if __name__ == "__main__":
    main()
