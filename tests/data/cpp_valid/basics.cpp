#include <iostream>
#include <string>
#include <vector>
#include <sstream>
#pragma once

using namespace std;
using std::vector;
using Names = std::vector<std::string>;

namespace shapes {

class Shape {
public:
    Shape(int sides) : sides_(sides) {}
    virtual ~Shape() {}
    virtual double area() const = 0;
    int sides() const { return sides_; }

protected:
    int sides_;
};

class Square : public Shape {
public:
    explicit Square(double side) : Shape(4), side_(side) {}
    double area() const override {
        return side_ * side_;
    }

private:
    double side_;
};

}  // namespace shapes

int add(int a, int b);
void greet(const std::string &name);
int count_items(const std::vector<int> &items);

int add(int a, int b) {
    return a + b;
}

void greet(const std::string &name) {
    std::cout << "Hello, " << name << "!" << std::endl;
}

int count_items(const std::vector<int> &items) {
    int total = 0;
    for (const auto &item : items) {
        total += item;
    }
    return total;
}

int main() {
    int a = 5;
    std::string name = "Ada";
    std::string copy(name);
    std::vector<int> values = {1, 2, 3};
    Names names;
    std::ostringstream out;
    int input = 0;

    cout << a << endl;
    cout << "a = " << a << ", sum = " << add(a, 2) << '\n';
    std::cerr << "warning" << std::endl;
    out << "total: " << count_items(values);
    std::cin >> input;
    greet(name);
    values.push_back(4);
    names.push_back(copy);

    shapes::Square square(2.0);
    cout << square.area() << endl;

    if (input > 0) {
        cout << "positive" << endl;
    } else if (input < 0) {
        cout << "negative" << endl;
    } else {
        cout << "zero" << endl;
    }

    while (a > 0) {
        a--;
    }

    return 0;
}
