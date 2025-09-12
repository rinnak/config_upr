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
		//обработка формата ${VAR}
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

vector<string> split_command(const string& input) { //разделение команды на части
	vector<string> tokens;
	stringstream stream(input);
	string token;
	while (stream >> token) {
		tokens.push_back(token);
	}
	return tokens;
}

void execute_ls(const vector<string>& tokens) {
	cout << "Команда ls выполнена ";
	if (tokens.size() > 1) {
		cout << "с аргументами: ";
		for (int i = 1; i < tokens.size(); i++) {
			cout << tokens[i];
			if (i < tokens.size() - 1) cout << " ";
		}
	}
	cout << endl;
}

void execute_cd(const vector<string>& tokens) {
	if (tokens.size() > 2) {
		cout << "Ошибка. Слмшком много аргументов для команды cd" << endl;
		return;
	}
	if (tokens.size() > 1) {
		if (tokens[1] == "-") {
			cout << "Команда cd выполнена. Переход в предыдущую директорию" << endl;
		}
		else if (tokens[1] == "~") {
			cout << "Команда cd выполнена. Переход в домашнюю директорию" << endl;
		}
		else cout<< "Команда cd выполнена. Переход в директорию: " << tokens[1] << endl;
	}
	else cout << "Команда cd выполнена. Переход в домашнюю директорию" << endl;
}

void run() {
	setlocale(0, "ru");
	cout << "Эмулятор командной строки UNIX" << endl;
	cout << "Напишите 'exit' для выхода или 'help' для справки"<<endl;
	string input;
	while (true) {
		cout << vfs_name << " $ ";
		if (!getline(cin, input)) {
			cout << endl << "Ошибка ввода или конец файла." << endl;
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
			cout << "Выход из эмулятора. Пока." << endl;
			break;
		}
		else if (command == "help") {
			cout << "Доcтупные команды :" << endl;
			cout << "  ls [аргументы]  - список файлов" << endl;
			cout << "  cd [директория] - смена директории" << endl;
			cout << "  exit            - выход из программы" << endl;
			cout << "  help            - показать справку" << endl;
		}
		else if (command == "ls") {
			execute_ls(tokens);
		}
		else if (command == "cd") {
			execute_cd(tokens);
		}
		else {
			cout << "Ошибка: неизвестная команда '" << command << "'" << endl;
			cout << "Введите 'help' для списка команд" << endl;
		}
	}
}
int main() {
	setlocale(0, "ru");
	run();
	return 0;
}