#include <iostream>
#include <memory>
#include <string>
#include <vector>
#include <map>

namespace geo {

struct Point {
    int x = 0;
    int y = 0;
};

enum class Kind { Circle, Square };

class Shape {
public:
    Shape() = default;
    Shape(const Shape &) = delete;
    virtual ~Shape() = default;
    virtual double area() const = 0;
    virtual std::string name() const
    {
        return "shape";
    }
protected:
    Kind kind_ = Kind::Circle;
};

class Circle : public Shape {
public:
    explicit Circle(double r)
        : radius_(r)
    {
    }
    double area() const override
    {
        return 3.14159 * radius_ * radius_;
    }
private:
    double radius_;
};

template <typename T>
class Box {
public:
    explicit Box(T value) : value_(value) {}
    T get() const { return value_; }
private:
    T value_;
};

}  // namespace geo

int add(int a, int b);
static void report(const std::string &label,
                   int value);

int add(int a, int b)
{
    return a + b;
}

static void report(const std::string &label,
                   int value)
{
    std::cout << label
              << ": "
              << value
              << std::endl;
}

struct Counter {
    int count;
} global_counter;

int main()
{
    std::vector<int> numbers{1, 2, 3};
    std::map<std::string, int> ages = {{"ada", 36}};
    std::unique_ptr<geo::Shape> shape = std::make_unique<geo::Circle>(2.0);
    geo::Box<int> box(5);
    geo::Point p{1, 2};
    auto twice = [](int v) { return v * 2; };
    int total = 0;
    int *ptr = &total;

    for (auto n : numbers) {
        total += twice(n);
    }
    std::cout << shape->area() << " " << box.get() << std::endl;
    std::cout << p.x << ages["ada"] << std::endl;
    *ptr += add(1, 2);
    report("total", total);
    global_counter.count = total;
    int *array = new int[3];
    delete[] array;
    if (total > 100)
        goto end;
    total--;
end:
    return 0;
}
