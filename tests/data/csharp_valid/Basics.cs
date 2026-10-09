using System;
using System.Collections.Generic;
using System.Linq;
using Alias = System.Text.StringBuilder;
using static System.Math;

#region Helpers
namespace Demo
{
    public class Counter
    {
        private int count;

        public int Count { get; private set; }
        public string Name { get; set; }

        public Counter(string name)
        {
            Name = name;
        }

        public void Increment()
        {
            count++;
            Count = count;
        }

        public int Twice(int value) => value * 2;
    }

    public static class Program
    {
        public static int Add(int a, int b)
        {
            return a + b;
        }

        public static void Log(params string[] lines)
        {
            foreach (var line in lines)
            {
                Console.WriteLine(line);
            }
        }

        public static async Task<int> LoadAsync(string path)
        {
            await Task.Delay(10);
            return path.Length;
        }

        public static async Task Main(string[] args)
        {
            int total = 0;
            var counter = new Counter("demo");
            var names = new List<string> { "a", "b" };
            Alias builder = new Alias();

            counter.Increment();
            total++;
            --total;
            new Counter("unused");
            Console.WriteLine($"Total: {total}");
            Console.WriteLine(args.Length);
            names.Add("c");
            builder?.Append("x");
            await LoadAsync("file.txt");
            var size = await LoadAsync("other.txt");
            Log("one", "two");

            using (var reader = new System.IO.StringReader("text"))
            {
                Console.WriteLine(reader.ReadLine());
            }

            foreach (var name in names.Where(n => n.Length > 0))
            {
                Console.WriteLine(name);
            }

            if (total > 0 && size > 0)
            {
                Console.WriteLine("ok");
            }
            else
            {
                Console.WriteLine("no");
            }
        }
    }
}
#endregion
