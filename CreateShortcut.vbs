Set sh = WScript.CreateObject("WScript.Shell")
sc = sh.CreateShortcut("%UserProfile%\Desktop\Cyber Nova.lnk")
sc.TargetPath = "C:\Users\pepin\cyber_nova\cyber_nova\CyberNova.exe"
sc.WorkingDirectory = "C:\Users\pepin\cyber_nova\cyber_nova"
sc.Save