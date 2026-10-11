// Classes, inheritance, templates and namespaces in C++.
#include <iostream>
#include <string>
#include <memory>

namespace shapes {

class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
    std::string describe() const { return "shape with area " + std::to_string(area()); }
};

class Circle : public Shape {
private:
    double radius_;

public:
    explicit Circle(double radius) : radius_(radius) {}
    double area() const override { return 3.14159 * radius_ * radius_; }
};

struct Point {
    int x = 0;
    int y = 0;
    Point operator+(const Point &other) const { return {x + other.x, y + other.y}; }
};

}  // namespace shapes

template <typename T>
T largest(T a, T b) {
    return a > b ? a : b;
}

template <typename T>
class Box {
public:
    explicit Box(T value) : value_(value) {}
    T get() const { return value_; }

private:
    T value_;
};

int main() {
    std::unique_ptr<shapes::Shape> shape = std::make_unique<shapes::Circle>(2.0);
    shapes::Point a{1, 2}, b{3, 4};
    shapes::Point c = a + b;
    Box<int> box(5);
    std::cout << shape->describe() << " " << c.x << " " << largest(3, 7)
              << " " << box.get() << std::endl;
    try {
        throw std::runtime_error("oops");
    } catch (const std::exception &error) {
        std::cout << error.what() << std::endl;
    }
    return 0;
}
