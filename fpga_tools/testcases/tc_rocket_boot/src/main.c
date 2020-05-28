
volatile unsigned long long *c = (unsigned long long*)0x10071000;


int main()
{
    int a = 10;
    int b = 4;

    *c = a + b;

    return *c;
}
