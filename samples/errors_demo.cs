// C# demo: common mistakes that SyntaxLens finds.
using System;

public class ErrorsDemo {
    public static void Main(string[] args) {
        int count = 10
        double price = 5 + * 2;
        string name = "Ada;
        char grade = 'AB';
        int 2nd = 3;
        if (count > 5 {
            Console.WriteLine("big");
        }
        for (int i = 0, i < 3, i++) {
            Console.WriteLine(i);
        }
        if count > 0 {
            count--;
        }
        int hex = 0xG1;
        while (count > 0);
        break;
    }
}