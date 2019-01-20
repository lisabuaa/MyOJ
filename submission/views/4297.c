#include <stdio.h>
int main()
{
	int x,y,z,sum;
	double avg;
	scanf("%d %d %d",&x,&y,&z);
	sum=x+y+z;
	avg=(x+y+z)/3.00;
	printf("%d\n%.2f",sum,avg);
}