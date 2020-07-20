from python_graphql_client import GraphqlClient
import feedparser
import httpx
import json
import pathlib
import re
import os

root = pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")

print(os.environ)
TOKEN = os.environ.get("ZWZ1437_TOKEN", "")


def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker),
        re.DOTALL,
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)


def make_query(after_cursor=None):
    return """
query {
  viewer {
    repositories(first: 100, privacy: PUBLIC, after:AFTER) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        name
        description
        url
        releases(last:1) {
          totalCount
          nodes {
            name
            publishedAt
            url
          }
        }
      }
    }
  }
}
""".replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )


def fetch_releases(oauth_token):
    repos = []
    releases = []
    repo_names = set()
    has_next_page = True
    after_cursor = None

    while has_next_page:
        data = client.execute(
            query=make_query(after_cursor),
            headers={"Authorization": "Bearer {}".format(oauth_token)},
        )
        print()
        print(json.dumps(data, indent=4))
        print()
        for repo in data["data"]["viewer"]["repositories"]["nodes"]:
            if repo["releases"]["totalCount"] and repo["name"] not in repo_names:
                repos.append(repo)
                repo_names.add(repo["name"])
                releases.append(
                    {
                        "repo": repo["name"],
                        "repo_url": repo["url"],
                        "description": repo["description"],
                        "release": repo["releases"]["nodes"][0]["name"]
                            .replace(repo["name"], "")
                            .strip(),
                        "published_at": repo["releases"]["nodes"][0][
                            "publishedAt"
                        ].split("T")[0],
                        "url": repo["releases"]["nodes"][0]["url"],
                    }
                )
        has_next_page = data["data"]["viewer"]["repositories"]["pageInfo"][
            "hasNextPage"
        ]
        after_cursor = data["data"]["viewer"]["repositories"]["pageInfo"]["endCursor"]
    return releases


def fetch_tils():
    sql = "select title, url, created_utc from til order by created_utc desc limit 5"
    return httpx.get(
        "https://til.simonwillison.net/til.json",
        params={"sql": sql, "_shape": "array", },
    ).json()


def fetch_blog_entries():
    entries = feedparser.parse("https://www.zhouwenzhen.top/atom.xml")["entries"]
    print(entries)
    return [
        {
            "title": entry["title"],
            "url": entry["link"].split("#")[0],
            "published": entry["published"].split("T")[0],
        }
        for entry in entries
    ]


if __name__ == "__main__":
    readme = root / "README.md"
    # project_releases = root / "releases.md"
    # releases = fetch_releases(TOKEN)
    # releases.sort(key=lambda r: r["published_at"], reverse=True)
    # md = "\n".join(
    #     [
    #         "* [{repo} {release}]({url}) - {published_at}".format(**release)
    #         for release in releases[:8]
    #     ]
    # )
    # readme_contents = readme.open(encoding='utf-8').read()
    # rewritten = replace_chunk(readme_contents, "recent_releases", md)
    #
    # # Write out full project-releases.md file
    # project_releases_md = "\n".join(
    #     [
    #         (
    #             "* **[{repo}]({repo_url})**: [{release}]({url}) - {published_at}\n"
    #             "<br>{description}"
    #         ).format(**release)
    #         for release in releases
    #     ]
    # )
    # project_releases_content = project_releases.open(encoding='utf-8').read()
    # project_releases_content = replace_chunk(
    #     project_releases_content, "recent_releases", project_releases_md
    # )
    # project_releases_content = replace_chunk(
    #     project_releases_content, "release_count", str(len(releases)), inline=True
    # )
    # project_releases.open("w").write(project_releases_content)
    #
    # tils = fetch_tils()
    # tils_md = "\n".join(
    #     [
    #         "* [{title}]({url}) - {created_at}".format(
    #             title=til["title"],
    #             url=til["url"],
    #             created_at=til["created_utc"].split("T")[0],
    #         )
    #         for til in tils
    #     ]
    # )
    # rewritten = replace_chunk(rewritten, "tils", tils_md)
    rewritten = "### Hi there 👋\n" \
                "I am CHOW!\n" \
                "- 🌱 I’m currently learning Flink and TensorFlow.\n" \
                "- 📫 How to reach me: [Email](mailTo:zhouwenzhen@outlook.com).\n\n" \
                "🚀 About my Blog:\n"
    entries = fetch_blog_entries()[:5]
    entries_md = "\n".join(
        ["- [{title}]({url}) - {published}".format(**entry) for entry in entries]
    )

    end = "\n --- \n" \
          "⭐From [zwz1437](https://github.com/zwz1437)\n"
    readme.open("w", encoding='utf-8').write(rewritten + entries_md + end)
