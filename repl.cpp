#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include <vector>
#include <sstream>
#include <string>
#include <cstdlib>
#include <cctype>
#include <map>
using namespace std;
string vfs_name = "mvfs";
string parse(const string& input) {
	string result;
	int pos = 0;
	while (pos < input.length()) {
		//��������� ������� ${VAR}
		if (pos + 1 < input.length() && input[pos] == '$' && input[pos + 1] == '{') {
			size_t end = input.find('}', pos + 2);
			if (end != string::npos) {
				string var_name = input.substr(pos + 2, end - pos - 2);
				const char* env_value = getenv(var_name.c_str());
				if (env_value) {
					result += env_value;
				}
				else {
					result += "${" + var_name + "}";
				}
				pos = end + 1;
				continue;
			}
		}
		else if (input[pos] == '$' && pos + 1 < input.length()) {
			int var_start = pos + 1;
			int var_end = var_start;
			while (var_end < input.length() && (isalnum(input[var_end]) || input[var_end] == '_')) {
				var_end++;
			}
			string var_name = input.substr(var_start, var_end - var_start);
			const char* env_value = getenv(var_name.c_str());
			if (env_value) {
				result += env_value;
			}
			else {
				result += "$" + var_name;
			}
			pos = var_end;
			continue;
		}
		result += input[pos];
		pos++;
	}
	return result;
}

vector<string> split_command(const string& input) { //���������� ������� �� �����
	vector<string> tokens;
	stringstream stream(input);
	string token;
	while (stream >> token) {
		tokens.push_back(token);
	}
	return tokens;
}

void execute_ls(const vector<string>& tokens) {
	cout << "������� ls ��������� ";
	if (tokens.size() > 1) {
		cout << "� �����������: ";
		for (int i = 1; i < tokens.size(); i++) {
			cout << tokens[i];
			if (i < tokens.size() - 1) cout << " ";
		}
	}
	cout << endl;
}

void execute_cd(const vector<string>& tokens) {
	if (tokens.size() > 2) {
		cout << "������. ������� ����� ���������� ��� ������� cd" << endl;
		return;
	}
	if (tokens.size() > 1) {
		if (tokens[1] == "-") {
			cout << "������� cd ���������. ������� � ���������� ����������" << endl;
		}
		else if (tokens[1] == "~") {
			cout << "������� cd ���������. ������� � �������� ����������" << endl;
		}
		else cout<< "������� cd ���������. ������� � ����������: " << tokens[1] << endl;
	}
	else cout << "������� cd ���������. ������� � �������� ����������" << endl;
}

void run() {
	setlocale(0, "ru");
	cout << "�������� ��������� ������ UNIX" << endl;
	cout << "�������� 'exit' ��� ������ ��� 'help' ��� �������"<<endl;
	string input;
	while (true) {
		cout << vfs_name << " $ ";
		if (!getline(cin, input)) {
			cout << endl << "������ ����� ��� ����� �����." << endl;
			break;
		}
		if (input.empty()) {
			continue;
		}
		vector<string> tokens = split_command(input);
		if (tokens.empty()) {
			continue;
		}
		for (string& token : tokens) {
			token = parse(token);
		}
		string command = tokens[0];
		if (command == "exit") {
			cout << "����� �� ���������. ����." << endl;
			break;
		}
		else if (command == "help") {
			cout << "��c������ ������� :" << endl;
			cout << "  ls [���������]  - ������ ������" << endl;
			cout << "  cd [����������] - ����� ����������" << endl;
			cout << "  exit            - ����� �� ���������" << endl;
			cout << "  help            - �������� �������" << endl;
		}
		else if (command == "ls") {
			execute_ls(tokens);
		}
		else if (command == "cd") {
			execute_cd(tokens);
		}
		else {
			cout << "������: ����������� ������� '" << command << "'" << endl;
			cout << "������� 'help' ��� ������ ������" << endl;
		}
	}
}
int main() {
	setlocale(0, "ru");
	run();
	return 0;
}