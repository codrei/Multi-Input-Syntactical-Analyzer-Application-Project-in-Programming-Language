// Classes, properties, interfaces, inheritance and exceptions in C#.
using System;
using System.Collections.Generic;

public interface IShape
{
    double Area();
    string Name { get; }
}

public abstract class Shape : IShape
{
    public string Name { get; protected set; } = "shape";
    public abstract double Area();
    public override string ToString() => $"{Name}: {Area():F2}";
}

public class Circle : Shape
{
    private readonly double radius;

    public Circle(double radius)
    {
        this.radius = radius;
        Name = "circle";
    }

    public double Radius
    {
        get { return radius; }
    }

    public override double Area() => Math.PI * radius * radius;
}

public enum Size { Small, Medium, Large }

public static class Program
{
    public static T Largest<T>(T a, T b) where T : IComparable<T>
    {
        return a.CompareTo(b) > 0 ? a : b;
    }

    public static void Main()
    {
        List<IShape> shapes = new List<IShape> { new Circle(2.0) };
        Dictionary<string, int> counts = new Dictionary<string, int>();
        counts["circle"] = shapes.Count;
        Func<int, int> square = n => n * n;
        Action<string> print = message => Console.WriteLine(message);

        foreach (IShape shape in shapes)
        {
            print(shape.ToString());
        }
        try
        {
            int zero = 0;
            Console.WriteLine(10 / zero);
        }
        catch (DivideByZeroException error)
        {
            Console.WriteLine("Cannot divide: " + error.Message);
        }
        finally
        {
            Console.WriteLine(Largest(3, 7) + square(4) + (int)Size.Medium);
        }
        if (shapes[0] is Circle circle)
        {
            Console.WriteLine(circle.Radius);
        }
    }
}
