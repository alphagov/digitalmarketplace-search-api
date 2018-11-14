# digitalmarketplace-search-api

[![Requirements Status](https://requires.io/github/alphagov/digitalmarketplace-search-api/requirements.svg?branch=master)](https://requires.io/github/alphagov/digitalmarketplace-search-api/requirements/?branch=master)

API to handle interactions between the digitalmarketplace applications and search.

- Python app, based on the [Flask framework](http://flask.pocoo.org/)

## Quickstart

Install [elasticsearch](http://www.elasticsearch.org/). This must be in the 5.x series; ideally 5.4 which is what we run on live systems.
```
brew update
brew cask install java
cd /usr/local/Homebrew/Library/Taps/homebrew/homebrew-core
git fetch --unshallow
git checkout d8c57e111f1990c0a33b0d73af818eb8d442b33b Formula/elasticsearch.rb # (version: 5.4.2)
HOMEBREW_NO_AUTO_UPDATE=1 brew install elasticsearch
git reset --hard master
```

### Install/Upgrade dependencies

Install Python dependencies with pip

```
make requirements-dev
```

### Run the tests

```
make test
```

### Run the development server

To run the Search API for local development you can use the convenient run
script, which sets the required environment variables for local development:
```
make run-app
```

More generally, the command to start the server is:
```
python application.py runserver
```

### Using the Search API locally

Start elasticsearch if not already running via brew (in a new console window/tab):

```bash
brew services start elasticsearch
< OR >
elasticsearch
```

The Search API runs on port 5001. Calls to the Search API require a valid bearer
token. For development environments, this defaults to `myToken`. An example request to your local search API
would therefore be:

```
curl -i -H "Authorization: Bearer myToken" 127.0.0.1:5001/g-cloud/services/search?q=email
```

### Updating application dependencies

`requirements.txt` file is generated from the `requirements-app.txt` in order to pin
versions of all nested dependecies. If `requirements-app.txt` has been changed (or
we want to update the unpinned nested dependencies) `requirements.txt` should be
regenerated with

```
make freeze-requirements
```

`requirements.txt` should be committed alongside `requirements-app.txt` changes.

### Updating the index mapping

The mapping JSON file is generated from framework data, and the originals reside alongside the framework data for the
latest relevant framework iteration in the
[frameworks repository](https://github.com/alphagov/digitalmarketplace-frameworks/).

For example, the `mappings/services.json` file was generated by the
[generate-search-config.py](https://github.com/alphagov/digitalmarketplace-frameworks/blob/master/scripts/generate-search-config.py)
script from an original mapping file
[frameworks/g-cloud-9/search_mapping.json](https://github.com/alphagov/digitalmarketplace-frameworks/blob/master/frameworks/g-cloud-9/search_mapping.json).

The mapping may need to be updated as a result of framework data changing, or to index new fields. Once the mapping file
has been generated (and has been deployed to the Search API server), this can be done by issuing a PUT request to the
existing index endpoint:

```
PUT /<index_name> HTTP/1.1
Authorization: Bearer myToken
Content-Type: application/json

{"type": "index", "mapping": "services"}
```

If the mapping cannot be updated in-place, [zero-downtime mapping update process](https://www.elastic.co/blog/changing-mapping-with-zero-downtime) should be used instead:

### Indexing data

On preview, staging and production, the overnight Jenkins jobs do not create new indices, but instead
overwrite whichever index the alias currently points to.

New indices are only created and aliased if the entire data set needs to be reindexed, e.g. following a
database reset or a change in the mapping. This is done with two scripts for each framework:

1. [index-to-search-service.py](https://github.com/alphagov/digitalmarketplace-scripts/blob/master/scripts/index-to-search-service.py)

   Create a new index, using the `index-name-YYYY-MM-DD` pattern for the new index name.

   ```
   ./scripts/index-to-search-service.py services dev
                                        --index=g-cloud-9-2018-01-01
                                        --frameworks=g-cloud-9
                                        --create-with-mapping=services
   ./scripts/index-to-search-service.py briefs dev
                                        --index=briefs-digital-outcomes-and-specialists-2018-01-01
                                        --frameworks=digital-outcomes-and-specialists
                                        --create-with-mapping=briefs-digital-outcomes-and-specialists-2
   ```
2. [update-index-alias.py](https://github.com/alphagov/digitalmarketplace-scripts/blob/master/scripts/update-index-alias.py)

   Update the alias to point to the new index (that has the date suffix):

   ```
   ./scripts/update-index-alias.py g-cloud-9 g-cloud-9-2018-01-01 <search-api-url>
   ./scripts/update-index-alias.py briefs-digital-outcomes-and-specialists briefs-digital-outcomes-and-specialists-2018-01-01 <search-api-url>
   ```

   This script also deletes the old index.
