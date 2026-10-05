// C++ demo: common mistakes that SyntaxLens finds.
#include <iostream>
#include <string>

int main() {
    int count = 10
    double price = 5 + * 2;
    std::string name = "Ada;
    char grade = 'AB';
    int 2nd = 3;
    if (count > 5 {
        std::cout << "big" << std::endl;
    }
    for (int i = 0, i < 3, i++) {
        std::cout << i << std::endl;
    }
    if count > 0 {
        count--;
    }
    int octal = 09;
    while (count > 0);
    break;
}