using System;
using System.Collections.Generic;
using System.Linq;

namespace Layouts
{
    public enum Level
    {
        Low,
        Medium,
        High
    }

    [Serializable]
    public class Repository<T>
        where T : class, new()
    {
        private readonly List<T> items = new List<T>();

        public int Count
        {
            get { return items.Count; }
        }

        public string Name { get; set; } = "repo";

        public void Add(T item)
        {
            items.Add(item);
        }

        public T Create() => new T();
    }

    public record Point(int X, int Y);

    public static class Program
    {
        public static int Square(int x)
        {
            return x * x;
        }

        public static void Main(string[] args)
        {
            var numbers = new List<int> { 5, 3, 8 };
            var big = numbers.Where(n => n > 4);
            var sorted = numbers
                .Where(n => n > 1)
                .OrderBy(n => n)
                .ToList();
            var ages = new Dictionary<string, int>
            {
                ["ada"] = 36,
                ["alan"] = 41
            };
            Level level = Level.High;
            string text = level == Level.Low ? "low" : "high";
            int total = 0;
            foreach (var n in big)
            {
                total += Square(n);
            }
            string path = @"C:\temp\file.txt";
            string message = $"Total: {total}";
            int? maybe = null;
            maybe ??= 4;
            var point = new Point(1, 2);
            if (int.TryParse("12", out var parsed))
            {
                total += parsed;
            }
            Console.WriteLine(message + path + maybe + point.X + sorted.Count + ages["ada"] + text);
        }
    }
}
