import json
import os

class RecordManager:
    def __init__(self, filename, record_dir):
        self.filename = filename
        self._load_records(record_dir, filename)

    def _load_records(self, record_dir, filename):
        self.filename = os.path.join(record_dir, filename)
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as file:
                    self.records = json.load(file)
            else:
                self.records = {}
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error loading records: {e}")
            self.records = {}

        self.verify_integrity(record_dir)
        try:
            if not os.path.exists(record_dir):
                os.makedirs(record_dir)
            if not os.path.exists(self.filename):
                with open(self.filename, 'w') as file:
                    json.dump({}, file)
        except OSError as e:
            print(f"Error creating directory or file: {e}")

    def _save_records(self):
        try:
            with open(self.filename, 'w') as file:
                json.dump(self.records, file, indent=4)
        except OSError as e:
            print(f"Error saving records: {e}")

    def add_record(self, key, value):
        try:
            if key == "Worlds":
                if key in self.records:
                    self.records[key].append(value)
                else:
                    self.records[key] = [value]
            else:
                self.records[key] = value
            self._save_records()
        except Exception as e:
            print(f"Error adding record: {e}")

    def rename_record(self, world_id, new_name):
        try:
            for key, value in self.records.items():
                if key.startswith("Worlds"):
                    for world in value:
                        if world['World ID'] == world_id:
                            world['World Name'] = new_name
                            self._save_records()
                            return
            raise ValueError("World ID not found in records")
        except Exception as e:
            print(f"Error renaming record: {e}")

    def remove_record(self, world_id):
        try:
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
        except Exception as e:
            print(f"Error removing record: {e}")

    def read_record(self, key):
        try:
            return self.records.get(key, None)
        except Exception as e:
            print(f"Error reading record: {e}")
            return None

    def read_all_records(self):
        try:
            return self.records
        except Exception as e:
            print(f"Error reading all records: {e}")
            return {}

    def verify_record(self, key):
        try:
            return key in self.records
        except Exception as e:
            print(f"Error verifying record: {e}")
            return False
    
    def record_exists(self, world_id):
        try:
            for key, value in self.records.items():
                if key.startswith("Worlds"):
                    for world in value:
                        if world['World ID'] == world_id:
                            return True
            return False
        except Exception as e:
            print(f"Error checking if record exists: {e}")

    def verify_integrity(self, directory):
        try:
            if not os.path.exists(directory) and self.records:
                with open(self.filename, 'w') as file:
                    json.dump({}, file)
            worlds = self.read_record("Worlds")
            if worlds is None:
                worlds = []
            illegal_entries = []
            for world in worlds:
                try:
                    if not os.path.exists(os.path.join(directory, world['World ID'])):
                        self.remove_record(world['World ID'])
                except KeyError:
                    illegal_entries.append(world)
            if illegal_entries:
                for entry in illegal_entries:
                    worlds.remove(entry)
                self._save_records()
        except Exception as e:
            print(f"Error verifying integrity: {e}")