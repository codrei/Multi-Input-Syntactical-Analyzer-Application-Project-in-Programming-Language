// Input/output, vectors, pointers, lambdas and raw strings in C++.
#include <iostream>
#include <string>
#include <vector>
#include <map>

using namespace std;

int square(int n) { return n * n; }

int main() {
    int x = 10;
    double average = 91.5;
    string name = "SyntaxLens";
    bool ok = true;
    auto total = 0;
    const int LIMIT = 1'000'000;

    vector<int> numbers = {5, 3, 8, 1};
    numbers.push_back(9);
    map<string, vector<int>> scores;
    scores["ada"] = {90, 95};

    for (int n : numbers) {
        total += n;
    }
    for (size_t i = 0; i < numbers.size(); ++i) {
        if (numbers[i] % 2 == 0) continue;
        cout << numbers[i] << " ";
    }
    cout << endl;

    if (x > 5 && ok) {
        cout << "Hello, " << name << "! Total: " << total << '\n';
    } else {
        cerr << "unexpected" << endl;
    }

    int *ptr = new int(42);
    int &ref = x;
    ref += *ptr;
    delete ptr;
    int *array = new int[3]{1, 2, 3};
    delete[] array;

    auto doubled = [](int v) { return v * 2; };
    string raw = R"(C:\path\with "quotes")";
    cout << square(doubled(3)) << average << LIMIT << raw.size() << nullptr << std::endl;
    return 0;
}
