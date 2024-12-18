import json
import os

class RecordManager:
    def __init__(self, filename, record_dir):
        self.filename = filename
        self._load_records(record_dir)

    def _load_records(self, record_dir):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                self.records = json.load(file)
        else:
            self.records = {}
        self.verify_integrity(record_dir)

    def _save_records(self):
        with open(self.filename, 'w') as file:
            json.dump(self.records, file, indent=4)

    def add_record(self, key, value):
        if key in self.records:
            if not isinstance(self.records[key], list):
                self.records[key] = [self.records[key]]
            self.records[key].append(value)
        else:
            self.records[key] = [value]
        self._save_records()
    
    def rename_record(self, world_id, new_name):
        for key, value in self.records.items():
            if key.startswith("Worlds"):
                for world in value:
                    if world['World ID'] == world_id:
                        world['World Name'] = new_name
                        self._save_records()
                        return
        raise ValueError("World ID not found in records")

    def remove_record(self, world_id):
        for key, value in self.records.items():
            if key.startswith("Worlds"):
                for world in value:
                    if world['World ID'] == world_id:
                        value.remove(world)
                        if len(value) == 0:
                            del self.records[key]
                        self._save_records()
                        return
        raise ValueError("World ID not found in records")

    def read_record(self, key):
        return self.records.get(key, None)
    
    def read_all_records(self):
        return self.records

    def verify_record(self, key):
        return key in self.records
    
    
    def verify_integrity(self, directory):
        missing_ids = []
        for key, value in self.records.items():
            if key.startswith("Worlds"):
                for world in value:
                    world_id = world['World ID']
                    if not os.path.exists(os.path.join(directory, world_id)):
                        missing_ids.append(world_id)
                        break
        for world_id in missing_ids:
            self.remove_record(world_id)