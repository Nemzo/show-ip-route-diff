## ⚙️ Configuration

Create a `hosts.json` file in the script directory to map IP addresses to hostnames.
```
{
    "192.168.1.1": "Cisco-Core-A",
    "10.0.0.254": "L3-Switch",
    "172.16.0.1": "FW"
}
```
## 📖 Usage
### Basic Command
```
sirdiff <Old_File> <New_File>
```
## 💡 Examples
1. **Show only the routes that actually changed**
    ```
    sirdiff route_old.txt route_new.txt -d
    ```
    
2. **Highlight exact character changes**
    ```
    sirdiff route_old.txt route_new.txt -d -i
    ```
    
3. **Filter by a specific subnet or hostname**
    ```
    sirdiff route_old.txt route_new.txt -g "10.20."
    ```
    
4. **Save the result as plain text**
    ```
    sirdiff route_old.txt route_new.txt -o diff_result.txt
    ```
    
5. **Export a Markdown table**
    ```
    sirdiff route_old.txt route_new.txt -d --md -o report.md
    ```
## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📝 License
This project is licensed under the **MIT License**.