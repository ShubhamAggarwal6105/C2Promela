int f(){
    int a[5];
    int n = 5;
    for(int i = 0;i<n;i++)
    {
        for (int j = 0; j < n - i - 1; j++)
        {
            if (a[j] > a[j + 1])
            {
                swap(a[j], a[j + 1]);
            }
        }
    }
}