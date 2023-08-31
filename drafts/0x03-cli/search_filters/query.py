from external_sources import DataStore

class Query:
    def __init__(self, data_store: DataStore):
        self.data_store = data_store

    def search(self, query: str, source: str = None):
        """Search for tracks based on metadata criteria."""
        results = []
        if source:
            data = self.data_store.get_metadata(source)
            for item in data:
                if query.lower() in item['title'].lower():
                    results.append(item)
        else:
            results = self.data_store.search_metadata(query)
        return results

    def filter(self, criteria: dict, source: str = None):
        """Filter tracks by multiple metadata criteria."""
        results = []
        if source:
            data = self.data_store.get_metadata(source)
            for item in data:
                match = True
                for key, value in criteria.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                if match:
                    results.append(item)
        else:
            for source, data in self.data_store.metadata.items():
                for item in data:
                    match = True
                    for key, value in criteria.items():
                        if key not in item or item[key] != value:
                            match = False
                            break
                    if match:
                        results.append(item)
        return results


if __name__ == '__main__':
    data_store = DataStore()
    data_store.add_metadata('source1', {'title': 'Track 1', 'artist': 'Artist 1', 'album': 'Album 1', 'genre': 'Genre 1'})
    data_store.add_metadata('source1', {'title': 'Track 2', 'artist': 'Artist 2', 'album': 'Album 2', 'genre': 'Genre 2'})
    data_store.add_metadata('source2', {'title': 'Track 3', 'artist': 'Artist 3', 'album': 'Album 3', 'genre': 'Genre 3'})

    query = Query(data_store)
    results = query.search('Track 1')
    print(results)
