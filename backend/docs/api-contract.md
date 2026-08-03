# GameGenie AI — API Contract

Base URL: `http://localhost:8000`

Every successful response wraps data in `{"success": true, ...}`.  
Every error uses the shape:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": null
  }
}
