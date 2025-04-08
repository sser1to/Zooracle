using Microsoft.EntityFrameworkCore;
using System.Data;
using backend.Models;
using Microsoft.Extensions.Configuration;

public class AppDbContext : DbContext
{
    private readonly IConfiguration _configuration;

    public AppDbContext(DbContextOptions<AppDbContext> options, IConfiguration configuration) : base(options)
    {
        _configuration = configuration;
    }

    public DbSet<animal_photos> animal_photos { get; set; }
    public DbSet<animal_types> animal_types { get; set; }
    public DbSet<animals> animals { get; set; }
    public DbSet<answer_options> answer_options { get; set; }
    public DbSet<favorite_animals> favorite_animals { get; set; }
    public DbSet<habitats> habitats { get; set; }
    public DbSet<question_answer> question_answer { get; set; }
    public DbSet<question_types> question_types { get; set; }
    public DbSet<questions> questions { get; set; }
    public DbSet<test_questions> test_questions { get; set; }
    public DbSet<test_score> test_score { get; set; }
    public DbSet<tests> tests { get; set; }
    public DbSet<users> users { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
    {
        if (!optionsBuilder.IsConfigured)
        {
            optionsBuilder.UseNpgsql(_configuration.GetConnectionString("DefaultConnection"));
        }
    }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // animal_photos
        modelBuilder.Entity<animal_photos>().HasKey(m => m.id);
        modelBuilder.Entity<animal_photos>().Property(m => m.id).ValueGeneratedOnAdd();

        // animal_types
        modelBuilder.Entity<animal_types>().HasKey(m => m.id);
        modelBuilder.Entity<animal_types>().Property(m => m.id).ValueGeneratedOnAdd();

        // animals
        modelBuilder.Entity<animals>().HasKey(m => m.id);
        modelBuilder.Entity<animals>().Property(m => m.id).ValueGeneratedOnAdd();
        modelBuilder.Entity<animals>()
            .HasOne(at => at.animal_type)
            .WithMany(a => a.animals)
            .HasForeignKey(at => at.animal_type_id)
            .OnDelete(DeleteBehavior.Cascade);

        // answer_options
        modelBuilder.Entity<animals>().HasKey(m => m.id);
        modelBuilder.Entity<animals>().Property(m => m.id).ValueGeneratedOnAdd();

        // favorite_animals
        modelBuilder.Entity<favorite_animals>().HasKey(m => m.id);
        modelBuilder.Entity<favorite_animals>().Property(m => m.id).ValueGeneratedOnAdd();
        modelBuilder.Entity<favorite_animals>()
            .HasOne(u => u.user)
            .WithMany(fa => fa.favorite_animals)
            .HasForeignKey(u => u.user_id)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<favorite_animals>()
            .HasOne(a => a.animal)
            .WithMany(f => f.favorite_animals)
            .HasForeignKey(a => a.animal_id)
            .OnDelete(DeleteBehavior.Cascade);

        // habitats
        modelBuilder.Entity<habitats>().HasKey(m => m.id);
        modelBuilder.Entity<habitats>().Property(m => m.id).ValueGeneratedOnAdd();

        // question_answer
        modelBuilder.Entity<question_answer>().HasKey(m => m.id);
        modelBuilder.Entity<question_answer>().Property(m => m.id).ValueGeneratedOnAdd();
        modelBuilder.Entity<question_answer>()
            .HasOne(q => q.question)
            .WithMany(qa => qa.question_answer)
            .HasForeignKey(q => q.question_id)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<question_answer>()
            .HasOne(ao => ao.answer_option)
            .WithMany(q => q.question_answer)
            .HasForeignKey(ao => ao.answer_id)
            .OnDelete(DeleteBehavior.Cascade);

        // question_types
        modelBuilder.Entity<question_types>().HasKey(m => m.id);
        modelBuilder.Entity<question_types>().Property(m => m.id).ValueGeneratedOnAdd();

        // questions
        modelBuilder.Entity<questions>().HasKey(m => m.id);
        modelBuilder.Entity<questions>().Property(m => m.id).ValueGeneratedOnAdd();
        modelBuilder.Entity<questions>()
            .HasOne(qt => qt.question_type)
            .WithMany(q => q.questions)
            .HasForeignKey(qt => qt.question_type_id)
            .OnDelete(DeleteBehavior.Cascade);

        // test_questions
        modelBuilder.Entity<test_questions>().HasKey(m => m.id);
        modelBuilder.Entity<test_questions>().Property(m => m.id).ValueGeneratedOnAdd();
        modelBuilder.Entity<test_questions>()
            .HasOne(q => q.question)
            .WithMany(tq => tq.test_questions)
            .HasForeignKey(q => q.question_id)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<test_questions>()
            .HasOne(ao => ao.test)
            .WithMany(t => t.test_questions)
            .HasForeignKey(ao => ao.test_id)
            .OnDelete(DeleteBehavior.Cascade);

        // test_score
        modelBuilder.Entity<test_score>().HasKey(m => m.id);
        modelBuilder.Entity<test_score>().Property(m => m.id).ValueGeneratedOnAdd();
        modelBuilder.Entity<test_score>()
            .HasOne(q => q.test)
            .WithMany(ts => ts.test_score)
            .HasForeignKey(q => q.test_id)
            .OnDelete(DeleteBehavior.Cascade);
        modelBuilder.Entity<test_score>()
            .HasOne(u => u.user)
            .WithMany(t => t.test_score)
            .HasForeignKey(u => u.user_id)
            .OnDelete(DeleteBehavior.Cascade);

        // tests
        modelBuilder.Entity<tests>().HasKey(m => m.id);
        modelBuilder.Entity<tests>().Property(m => m.id).ValueGeneratedOnAdd();

        // users
        modelBuilder.Entity<users>().HasKey(m => m.id);
        modelBuilder.Entity<users>().Property(m => m.id).ValueGeneratedOnAdd();
    }
}