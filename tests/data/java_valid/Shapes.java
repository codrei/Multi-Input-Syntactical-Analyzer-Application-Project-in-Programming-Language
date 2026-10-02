// Classes, interfaces, enums, inheritance and generics.
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

interface Shape {
    double area();

    default String describe() {
        return "Shape with area " + area();
    }
}

enum Color { RED, GREEN, BLUE }

enum Size {
    SMALL("S"), LARGE("L");

    private final String code;

    Size(String code) {
        this.code = code;
    }

    public String getCode() {
        return code;
    }
}

abstract class Base implements Shape {
    protected String name;

    Base(String name) {
        this.name = name;
    }

    public abstract double area();
}

class Circle extends Base {
    private final double radius;

    Circle(double radius) {
        super("circle");
        this.radius = radius;
    }

    @Override
    public double area() {
        return Math.PI * radius * radius;
    }
}

class Box<T extends Comparable<T>> {
    private T value;

    Box(T value) {
        this.value = value;
    }

    public static <E extends Comparable<E>> E max(List<E> items) {
        E best = items.get(0);
        for (E item : items) {
            if (item.compareTo(best) > 0) {
                best = item;
            }
        }
        return best;
    }

    public T get() {
        return value;
    }
}

public class Shapes {
    public static void main(String[] args) {
        List<Shape> shapes = new ArrayList<>();
        shapes.add(new Circle(2.0));
        Map<String, List<Integer>> scores = new HashMap<>();
        scores.put("ada", new ArrayList<>());
        Box<Integer> box = new Box<>(5);
        int[] numbers = {4, 8, 15, 16, 23, 42};
        int[][] grid = new int[3][4];
        String[] names = new String[] {"a", "b"};
        Object shape = shapes.get(0);
        if (shape instanceof Circle circle) {
            System.out.println(circle.describe());
        }
        System.out.println(box.get() + numbers.length + grid[0].length + names.length);
        System.out.println(Color.RED + " " + Size.SMALL.getCode());
    }
}
