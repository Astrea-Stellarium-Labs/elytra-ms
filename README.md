# elytra-ms
A Python Library for various Microsoft APIs, including the Xbox and Bedrock Realms APIs.

**Note: this library is a work in progress!** This currently only supports the workflow [the Realms Playerlist Bot](https://github.com/AstreaTSS/RealmsPlayerlistBot) does, but it is planned to be expanded in the future.

## Usage

```python
import asyncio
import elytra

async def main():
    xbox_api = await elytra.XboxAPI.from_file("CLIENT_ID", "CLIENT_SECRET", oauth_path="oauth.json")
    print(await xbox_api.fetch_profile_by_gamertag("SomeGamertag"))
    await xbox_api.close()

asyncio.run(main())
```

## Setup

TODO: actually do this section.

### Install Package

Requires Python 3.10+.

```sh
pip install -U elytra-ms
```

### Make An Application

> Taken from [xbox-webapi-python](https://github.com/OpenXbox/xbox-webapi-python) for now, copyright 2020 OpenXbox under MIT.

Authentication is supported via OAuth2.

- Register a new application in [Azure AD](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade).
  - Name your app.
  - Select "Personal Microsoft accounts only" under supported account types.
  - Add <http://localhost/auth/callback> as a Redirect URI of type "Web."
- Copy your Application (client) ID for later use.
- On the App Page, navigate to "Certificates & secrets."
  - Generate a new client secret and save for later use.

### Get OAuth/Token Data

In your terminal, run:

```sh
elytra-authenticate --client-id CLIENT_ID_FROM_ABOVE --client-secret CLIENT_SECRET_FROM_ABOVE
```

This will create a file called `oauth.json` in the directory this is run in. This file alone works with all APIs currently supported.