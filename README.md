⚙️ Configuration
Create a hosts.json file in the script directory to map IP addresses to hostnames.

JSON
{
    "192.168.1.1": "Cisco-Core-A",
    "10.0.0.254": "L3-Switch-Osaka",
    "172.16.0.1": "FW-Tokyo"
}
📖 Usage
Basic Command
Bash
sirdiff <Old_File> <New_File>
💡 Examples
Show only the routes that actually changed

Bash
sirdiff route_old.txt route_new.txt -d
Highlight exact character changes

Bash
sirdiff route_old.txt route_new.txt -d -i
Filter by a specific subnet or hostname

Bash
sirdiff route_old.txt route_new.txt -g "10.20."
Save the result as plain text

Bash
sirdiff route_old.txt route_new.txt -o diff_result.txt
Export a Markdown table

Bash
sirdiff route_old.txt route_new.txt -d --md -o report.md
🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

📝 License
This project is licensed under the MIT License.