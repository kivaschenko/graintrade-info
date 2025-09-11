from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    @abstractmethod
    def parse(self) -> List[Dict[str, Any]]:
        pass

    def save_results(
        self, results: List[Dict[str, Any]], filepath: str, file_ext: str = "json"
    ) -> None:
        if file_ext != "json":
            raise ValueError("Currently only 'json' file extension is supported.")
        print(f"Saving results to {filepath}...")
        print(f"Total records to save: {len(results)}")
        print(
            f"First record preview: {results[0] if results else 'No records to display'}"
        )
        import json

        with open(filepath, "w", encoding="utf-8") as f:
            # json.dump(results, f, ensure_ascii=False, indent=4)
            f.write(json.dumps(results, ensure_ascii=False, indent=4))
            print(f"Results saved to {filepath}")
